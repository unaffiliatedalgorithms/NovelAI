import MemoryBase
import NovelLLM
import Algorithms
import Refinement
import config
import time

# MemoryBase requires a Table "Note" with text fields "Title" and "Category"

def query_forced(question,mb,ai,table_name="Note",history="",top_k=5,max_k=-1,expand=0.3,nquer=[3,4],fquer=[3,4]):
	if(max_k<0):
		max_k = len(mb.embedders.weights)*-max_k*top_k
	answer = query(question,mb,ai,table_name,top_k,max_k,expand)
	print("Query:")
	print(question)
	print("Answer:")
	print(answer)
	if(query_answered(question,answer,ai)):
		print("answered")
		text = query2note(question,answer,ai)
		text = Refinement.find_error(text,mb,ai,table_name,nquer=fquer)
		print(merge2db(text,mb,ai,table_name))
	else:
		print("inventing")
		answer = invent(question,answer,history,mb,ai,table_name,nquer=nquer,fquer=fquer)
		print(answer)
		print("invented")
		text = query2note(question,answer,ai)
		text = Refinement.find_error(text,mb,ai,table_name,top_k,max_k,expand,nquer=fquer)
		print(merge2db(text,mb,ai,table_name))
	return text

def query(question,mb,ai,table_name="Note",top_k=5,max_k=-1,expand=0.3):
	if(max_k<0):
		max_k = len(mb.embedders.weights)*-max_k*top_k
	# initiate scratchpad with text describing empty state
	scratchpad = "There is currently no partial information to answer the query."
	# get the texts which are closest to the query text
	# queries are intended for searches against the note table in the db of the memory base
	matches = mb.similarity_search(table_name,question,top_k,max_k)
	relevant = []
	answered = []
	for i in matches:
		relevant.append(is_relevant(question,i[1],ai))
	for i in matches:
		answered.append(query_answered(question,i[1],ai))
	print("Current query:\n"+question)	
	print("Matches answer question")
	print(answered)
	print("Matches are relevant to question")
	print(relevant)
	if(sum(answered)==0):
		l = len(matches)
		r2 = relevant[int(l/2):]
		if(top_k<=l and expand>0 and expand<=sum(r2)/len(r2)):
			return query(question,mb,ai,table_name,top_k*2,max_k*2,expand)
	for i in range(len(matches)):
		if(relevant[i]):
			messages = [
				    {"role": "system", "content": """You are an AI specialized in answering queries. You're given a query, a partial answer to the query and a series of text snippets which might help improve or expand the answer. Your task is to improve and expand the answer based on anything you can deduce from the snippet. Be creative in using inference from related topics, but do not invent. If you have nothing to add, retain the previous answer. Keep the answer as concise as possible and retain any and all potential relevant information from the previous answer."""+config.style_guide+"""the partial answer and snippet. """},
				    {"role": "user", "content": "Query:\n"+question+"\nPartial Answer:\n"+scratchpad+"\nSnippet:\n"+matches[i][1]},
				    {"role": "system","content":""}
				]
			scratchpad = ai.instruct.chat(messages)
	messages = [
				    {"role": "system", "content": """You're an AI specialized in answering queries. You're given a query and a partial answer to the query. Your task is to formulate a proper reply to the query given the information in the partial answer. Write an answer, possibly including speculation, based on the partial answer. Do not invent an aswer. The answer must only contain information derived from the partial answer. Take care to verify your reply properly addresses the query and uses sound and consistent logic."""+config.style_guide+"""the partial answer."""},
				    {"role": "user", "content": "Query:\n"+question+"\nPartial Answer:\n"+scratchpad},
				    {"role": "system","content":""}
				]
	scratchpad = ai.instruct.chat(messages)
	return scratchpad
	
def query_answered(query,answer,ai):
	messages = [
			    {"role": "system", "content": """You are an AI specialized in evaluating query responses. You are given an a query as well as a response. Your task is to state if the reply addresses the query in an satisfactory manner. Stating no information found is not adequate. Reply with either "yes" or "no" and nothing else."""},
			    {"role": "user", "content": "Query:\n"+query+"\nReply:\n"+answer},
			    {"role": "system","content":""}
			]
	answered = ai.instruct.chat(messages)
	if(answered=="yes"):
		return True
	else:
		return False
	
def is_relevant(query,answer,ai):
	messages = [
			    {"role": "system", "content": """You are an AI tasked with evaluating if a text contains any information for responding to a query. You are given the query and a text. Answer if the text has any information to that can add to a reply or to speculation. Answer only with "yes" or "no" and nothing else. Consider imaginative requests more likely to receive a yes."""},
			    {"role": "user", "content": "Query:\n"+query+"\nText:\n"+answer},
			    {"role": "system","content":""}
			]
	relevant = ai.instruct.chat(messages)
	if(relevant=="yes"):
		return True
	else:
		return False

def invent(question,answer,history,mb,ai,table_name="Note",top_k=5,max_k=-1,expand=0.3,nquer=[3,4],fquer=[3,4]):
	if(max_k<0):
		max_k = len(mb.embedders.weights)*-max_k*top_k
	background = answer
	while(gather_info(question,background,history,ai)):
		questions = ask_questions(question,background,history,ai,nquer[0],nquer[1])
		print(questions)
		answers = []
		history = update_history(question,background,history,ai)
		print("History:\n"+history)
		for q in questions:
			answers.append(query_forced(q,mb,ai,table_name,history,top_k,max_k,expand,nquer=nquer,fquer=fquer))
		background = pool_questions(question,questions,answers,background,ai)
		print("Accumulated background information:")
		print(background)
	answer = invent_answer(question,background,ai)
	print("Invented answer:")
	print(answer)
	return answer
	
def pool_questions(question,questions,answers,background,ai):
	for i in range(len(questions)):
		messages = [
			    {"role": "system", "content": """You are an AI tasked with creating or completing answers to questions with limited information. You are given an initial query and a background text with accumulated knowledge to work on generating a reply. You are also given a supporting question along with its answer. Your task is to pull any information from the supporting question and its answer and merge it into the background text. You may use vague conjectures and inference to speculate towards an answer to the initial query. """+config.style_guide+""" the background and support answer."""},
			    {"role": "user", "content": "Initial Query:\n"+question+"\nBackground Text:\n"+background+"\nSupport Question:\n"+questions[i]+"\nSupport Answer:\n"+answers[i]},
			    {"role": "system","content":""}
			]
		background = ai.instruct.chat(messages)
	return background

def invent_answer(question,background,ai):
	messages = [
			    {"role": "system", "content": """You are an AI tasked with creating or completing replies to queries with limited information. You are given an initial query and a background text with accumulated knowledge to work on generating a reply. Answer the given query in a satisfactory manner. Improvise and fabricate any additional information that will complete the reply to the query, without contradicting the background text."""+config.style_guide+"""the background text and query."""},
			    {"role": "user", "content": "Query:\n"+question+"\nBackground:\n"+background},
			    {"role": "system","content":""}
			]
	return ai.instruct.chat(messages)
	
def gather_info(question,background,history,ai):
	messages = [
			    {"role": "system", "content": """You are an AI tasked with creating or completing replies to queries with limited information. You are given a query and a background text with accumulated knowledge to work on inventing a reply. You are also given the history of all queries and replies until now. Your task is to determine if additional questions should be asked or if if there is sufficient information to invent an answer to the current query. The longer the list of question/answer pairs in the history is, the more hard-pressed you become to choose "invent". Answer only with "ask" or "invent" and nothing else."""},
			    {"role": "user", "content": "Query:\n"+question+"\nText:\n"+background+"\nHistory:\n"+history},
			    {"role": "system","content":""}
			]
	gather = ai.instruct.chat(messages)
	if(gather=="ask"):
		return True
	else:
		return False

def ask_questions(question,background,history,ai,low=3,high=5):
	messages = [
			    {"role": "system", "content": """You are an AI tasked with approaching challenging queries. You are given a query (regarding a novel in the writing), a partial reply to the query and a history of all queries and replies. Generate a heuristic inquiry consisting of """+str(low)+""" to """+str(high)+""" extrapolative queries that explore topics reaching beyond the previous queries. The more queries that are unanswered the more divergent, overarching and general the generated queries should be. Consider asking about settings, characters, chronology, keywords, etc.
			    Only list the queries. Do not include explanations, assumptions, or any additional output."""},
			    {"role": "user", "content": "Query:\n"+question+"\nPartial Reply:\n"+background+"\nHistory:\n"+history},
			    {"role": "system","content":""}
			]
	question_text = ai.instruct.chat(messages)
	print(question_text)
	question_list = ai.split2questions(question_text)
	questions = ai.split2list(question_list)
	return questions
	
def update_history(question,reply,history,ai):
	messages = [
			    {"role": "system", "content": """You are an AI tasked with keeping track of all queries and all replies generated until now. You are given a query, its reply and a list of previous query/reply pairs (History). Write the history as is, and append the the new query and its reply."""},
			    {"role": "user", "content": "Query:\n"+question+"\nReply:\n"+reply+"\nHistory:\n"+history},
			    {"role": "system","content":""}
			]
	return ai.instruct.chat(messages)

def query2note(query,answer,ai):
	messages = [
			    {"role": "system", "content": """You are an AI assistant tasked with transforming query-answer pairs into concise, informative statements. Given a query and its corresponding answer, generate a text that presents all the information clearly and objectively without phrasing it as a query."""+config.note_guide},
			    {"role": "user", "content": "Query:\n"+query+"\nAnswer:\n"+answer},
			    {"role": "system","content":""}
			]
	return ai.instruct.chat(messages)
	

def merge2db(text,mb,ai,table_name="Note",top_k=3,max_k=-1):
	if(max_k<0):
		max_k = len(mb.embedders.weights)*-max_k*top_k
	mb.reindex_embeddings("Note")
	title = create_title(text,ai)
	category = create_category(text,ai)
	new = "Title: "+title+"\nCategory: "+category+"\n"+text
	matches = mb.similarity_search(table_name,new,columns=["embedding_text","title","category"],top_k=top_k,max_k=max_k)
	for i in matches:
		old = "Title: "+i[2]+"\nCategory: "+i[3]+"\n"+i[1]
		messages = [
			    {"role": "system", "content": """You are an AI assistant tasked with integrating a text into a text database. You are given an old and a new text each with title and category. Take into account that the text database and its entries should remain individually compact and minimally redundant. Choose one of the following options:
			    "merge": if the texts are not long and overwhelmingly redundant; or both texts are short and either focuses on a list which would naturally expand with the other
			    "partition": if the texts are more similar to each other than the content of each text is to itself; or if the combined content of both texts could be split into two texts which are more distinct and atomic than the current texts; or either text contains content that would fit better within the other text
			    "add": if the texts are atomic in relation a specific topic, category, proper noun, or group of proper nouns; or are more self-contained than if they would be merged together.
			    "prune": if the new text is exclusively a rephrasing of part or all of the old text and contains no details beyond that
			    Reply with one of the options "merge", "partition", "add" or "prune" and nothing else."""},
			    {"role": "user", "content": "New Text:\n"+new+"\nOld Text:\n"+old},
			    {"role": "system","content":""}
			]
		action = ai.instruct.chat(messages)
		print("Entry with id: "+str(i[0]))
		s = mb.index_counters[table_name]["size"]
		adop = mb.index_counters[table_name]["deletions"]+mb.index_counters[table_name]["additions"]
		if((s<=100 and adop>s*0.5)or(s>100 and adop>s*0.2)):
			print(str(adop)+" deletions and additions were performed since last reindexing. Current table size is "+str(s))
			sanitize_mb(mb,ai,table_name=table_name,num_sim=2)
		print(action)
		if(action=="merge"):
			merged = merge_texts(old,new,ai)
			merged = clean_text(merged,ai)
			title = create_title(merged,ai)
			category = create_category(merged,ai)
			mb.update_embeddings(table_name,merged,i[0],{"Title":title,"Category":category})
			if(split_check(merged,ai)):
				print("Merge leading to split")
				split_text(merged,mb,ai,i[0],table_name=table_name)
			return "Merged with note id "+str(i[0])+"."
		elif(action=="partition"):
			partitions = partition_texts(old,new,ai)
			title = create_title(partitions[0],ai)
			category = create_category(partitions[0],ai)
			mb.update_embeddings(table_name,partitions[0],i[0],{"Title":title,"Category":category})
			partitions[1] = clean_text(partitions[1],ai)
			title = create_title(partitions[1],ai)
			category = create_category(partitions[1],ai)
			mb.add_embeddings(table_name,partitions[1],{"Title":title,"Category":category})
			return "Text partitioned with text in database with id "+str(i[0])+"."
		elif(action=="ignore"):
			print(old)
			print(new)
			return "Text discarded due to full redundancy."
	id = mb.add_embeddings(table_name,text,{"Title":title,"Category":category})
	if(split_check(text,ai)):
		split_text(text,mb,ai,i[0],table_name=table_name)
	return "Text added to database."
	
def merge_texts(old,new,ai):
	messages = [
				{"role": "system", "content": """You are an AI assistant tasked merging two texts. You are given two texts and should merge them a single text containing all relevant information. Remove any titles and categories headers from the merged text. Ensure that no details is lost during the merging."""+config.note_guide},
				{"role": "user", "content": "First Text:\n"+old+"\nSecond Text:\n"+new},
				{"role": "system","content":""}
				]
	return ai.instruct.chat(messages)

def partition_texts(old,new,ai):
	messages = [
				{"role": "system", "content": """You are an AI designed to merge, reorganize and harmonize overlapping information from two texts. Your task is to consolidate all relevant details and then redistribute the content based on the current categories and titles. Identify overlapping, similar and unique content. Combine information where needed while eliminating redundancy. Every piece of information should be assigned to the most fitting category and title. Avoid separating lists.
Ensure that no details are lost during the split. It is fine if both partions remain the same as the current texts."""+config.note_guide},
				{"role": "user", "content": "First Text:\n"+old+"\nSecond Text:\n"+new},
				{"role": "system","content":""}
				]
	text = ai.instruct.chat(messages)
	partitioned = ai.split2sections(text,2)
	partitions = ai.split2list(partitioned)
	for i in range(len(partitions)):
		partitions[i] = clean_text(partitions[i],ai)
	if(len(partitions)>2):
		print("In partition_texts: The text was split into more than two parts... Content will be lost")
	return partitions
	
def partion_text(text,ai):
	messages = [
				{"role": "system", "content": """You are an AI designed to partition a single text into two texts. You are given an input text and should determine the most fitting, categorically distinct and non redundant texts that can be generated from the text. Reorganize and distribute content into the partitions according to fitting subjects and categories. Ensure that no details are lost during the split. Each partition needs to be coherent and make sense without requiring the other partition. Avoid separating list elements."""+config.note_guide},
				{"role": "user", "content": "Text:\n"+text},
				{"role": "system","content":""}
				]
	text = ai.instruct.chat(messages)
	partitioned = ai.split2sections(text,2)
	partitions = ai.split2list(partitioned)
	for i in range(len(partitions)):
		partitions[i] = clean_text(partitions[i],ai)
	if(len(partitions)>2):
		print("In partition_text: The text was split into more than two parts... Content will be lost")
	return partitions
	
def create_title(text,ai):
	messages = [
			    {"role": "system", "content": """You are an AI assistant tasked with extracting the title from a text. You are given a text and should reply with the title of the text. If the title is not within the text create a short and fitting title for it. Return only the title and nothing else."""},
			    {"role": "user", "content": "Text:\n"+text},
			    {"role": "system","content":""}
			]
	return ai.instruct.chat(messages)
	
def create_category(text,ai):
	messages = [
			    {"role": "system", "content": """You are an AI assistant tasked with determining the narrative metadata category of a text snippet. You are given a text and should reply with the category and specialized subcategory of the text. If the category is not within the text detemine an appropriate category of a narrative element. Return only the category-subcategory and nothing else."""},
			    {"role": "user", "content": "Text:\n"+text},
			    {"role": "system","content":""}
			]
	return ai.instruct.chat(messages)
	
def clean_text(text,ai):
	messages = [
			    {"role": "system", "content": """You are an AI assistant tasked with restructuring and cleaning texts. You are given a input text. Rewrite the the text to guaranty the same structure throughout the text. Retain all details from the text. Remove any headers and titles/categories at the beginning of the text."""+config.note_guide},
			    {"role": "user", "content": "Text:\n"+text},
			    {"role": "system","content":""}
			]
	return ai.instruct.chat(messages)
	
def sanitize_mb(mb,ai,table_name="Note",num_sim=1,num_rep=1):
	mb.vacuum_table(table_name)
	# maybe running this multiple times will help refine the structure of the memorybase
	for i in range(num_rep):
		# work on removing duplicates and similarities 
		merge_loop(mb,ai,table_name,num_sim)
		# split texts into more elementary parts
		split_loop(mb,ai,table_name)

def split_text(text,mb,ai,id,table_name="Note"):
	parts = partion_text(text,ai)
	title = create_title(parts[0],ai)
	category = create_category(parts[0],ai)
	mb.update_embeddings(table_name,parts[0],id,{"Title":title,"Category":category})
	title = create_title(parts[1],ai)
	category = create_category(parts[1],ai)
	id= mb.add_embeddings(table_name,parts[1],{"Title":title,"Category":category})
	return id
	
def split_loop(mb,ai,table_name="Note"):
	print("Splitting Loop")
	ids = mb.get_all_id(table_name)
	ids = Algorithms.dl_dict(ids)
	while(ids.len>0):
		id = ids.head
		text = mb.get_fields(table_name,id,["embedding_text"])[0]
		if(split_check(text,ai)):
			id2 = split_text(text,mb,ai,id,table_name=table_name)
			ids.insert_tail(id2)
		else:
			ids.delete(id)
			id = ids.head
	mb.reindex_embeddings(table_name,0,p=0)
	
def merge_loop(mb,ai,table_name="Note",num_sim=1):
	print("Merging Loop")
	ids = mb.get_all_id(table_name)
	ids = Algorithms.dl_dict(ids)
	while(ids.len>0):
		id1 = ids.head
		f = mb.get_fields(table_name,id1,["title","category","embedding_text"])
		text1 = "Title: "+f[0]+"\nCategory: "+f[1]+"\n"+f[2]
		matches = mb.similarity_search(table_name,text1,top_k=num_sim+1,max_k=(num_sim+1)*len(mb.embedders.weights),columns=["title","category","embedding_text"])
		index = 0
		while(index<len(matches)):
			
			while(matches[index][0]==id1 and index<len(matches)):
				index+=1
			if(index>=len(matches)):
				break
			id2 = matches[index][0]
			text2 = "Title: "+matches[index][1]+"\nCategory: "+matches[index][2]+"\n"+matches[index][3]
			action = refactor(text1,text2,ai)
			if(action=="merge"):
				text = merge_texts(text1,text2,ai)
				title = create_title(text,ai)
				category = create_category(text,ai)
				mb.update_embeddings(table_name,text,id1,{"Title":title,"Category":category})
				# implement function in mb to remove row with id
				mb.delete_row(table_name,id2)
				ids.delete(id2)
				break
			elif(action=="partition"):
				parts = partition_texts(text1,text2,ai)
				title = create_title(parts[0],ai)
				category = create_category(parts[0],ai)
				mb.update_embeddings(table_name,parts[0],id1,{"Title":title,"Category":category})
				title = create_title(parts[1],ai)
				category = create_category(parts[1],ai)
				mb.update_embeddings(table_name,parts[1],id2,{"Title":title,"Category":category})
				ids.insert_tail(id2)
				break
			index+=1
		if(index>=len(matches)):
			ids.delete(id1)
	mb.reindex_embeddings(table_name,0,p=0)
	
def split_check(text,ai):
	messages = [
			    {"role": "system", "content": """You are an AI assistant tasked with determining if a text should be split into two pieces or not. You are given a text as input. The text should be split if the text is long; or the text can be partitioned into two fully independent and atomic texts which do no require the context of the other for comprehension and completeness. Do not split single lists or single topic overviews (unless very long). Choose to split the text or keep it in one piece. Choose "split" or "keep" and nothing else."""},
			    {"role": "user", "content": "Text:\n"+text},
			    {"role": "system","content":""}
			]
	if(ai.instruct.chat(messages)=="keep"):
		return False
	else:
		return True
	
def refactor(text1,text2,ai):
	messages = [
			    {"role": "system", "content": """You are an AI assistant tasked managing related texts inside a collection. You are given two texts, both with title and category. Choose one of the following options:
			     "merge": if the texts are overwhelmingly redundant; or both are short and focus on a list which would be a natural expansion of the other or if both texts focus on the exact same proper noun or groups of proper nouns
			    "partition": if the texts are more similar to each other than the content of each text is to itself; or if the provided content of both texts could be split into two texts which are more distinct and atomic than the current texts and noticably different from these; or either text contains content that would clearly fit better inside the other
			    "separate": if texts are atomic regarding a specific topic, category or proper noun, or relationship of proper nouns; or are more self-contained than if they would be merged together
			    The goal is to group and separate information such that texts are distinct, compact and self-contained.
			    Reply with one of the options "merge", "partition" or "separate" and nothing else."""},
			    {"role": "user", "content": "First Text:\n"+text1+"\nSecond Text:\n"+text2},
			    {"role": "system","content":""}
			]
	#print(explain(text1,text2,ai))
	action =ai.instruct.chat(messages)
	return action	



fantasy_snippets = [
    "In the ancient kingdom of Eldoria, the mighty warrior Altharion wielded his enchanted sword, Nightfang, against the Shadow Horde.",
    "Lady Sylwen of the Moonveil Forest was known for her wisdom, her silver hair flowing like moonlight in the wind.",
    "The dark sorcerer Vaelgor sought the lost relic of Zyphoros hidden deep within the ruins of Arkanvale.",
    "Prince Kaelen of Drakenshade rode atop his crimson wyvern, Valdris, soaring above the clouds of the Ember Peaks.",
    "The rogue assassin Seraphine Darkwhisper moved silently through the alleys of Blackthorn Keep, seeking her next target.",
    "Grand Magister Orynthos deciphered the ancient runes of Aetherhall, revealing secrets lost for millennia.",
    "Deep in the Mistwood, the enigmatic ranger Thalorin tracked the elusive silver stag of legend.",
    "Queen Elowen of Starfall Keep gazed into the Astral Mirror, seeking visions of the world's fate.",
    "The mighty dwarf smith Grumgar Ironfist forged the legendary battle-axe, Stormcleaver, in the heart of Mount Brimstone.",
    "High Priestess Lyra Moonshadow chanted sacred hymns within the ethereal halls of the Celestial Temple.",
    "Sir Garrik Stormbane stood vigil at the gates of Frostholm, waiting for the inevitable onslaught of the Iceborn.",
    "The mischievous bard Callidus Ravensong strummed his lute in the bustling markets of Windmere, singing tales of adventure.",
    "Eldrin the Arcane, last of the Starborn, channeled cosmic energies to defend the city of Everreach.",
    "The pirate queen, Isolde Blacktide, ruled the Azure Isles with an iron fist and a heart of gold.",
    "Atop the floating spire of Zephyria, Archmage Vorlan contemplated the mysteries of the multiverse.",
    "The mysterious alchemist Zepharion concocted potions of immense power in his hidden laboratory beneath the sands of Jador.",
    "In the twilight realm of Nythalor, the shadow priestess Selene Darkspire wove spells of dread and desire.",
    "The wandering knight Sir Eryndor Ravenshield embarked on a quest to reclaim the lost banner of his fallen house.",
    "Within the whispering caves of Eldros, the half-elf rogue Kyris Shadowstep uncovered secrets that should have remained buried.",
    "From the burning deserts of Solareth, the fire mage Azura Flameheart emerged, wielding the essence of the sun itself."
]

'''
a = time.time()
nllm_param = {'default_model':{'path':"/llm/Replete-LLM-V2.5-Qwen-32b-Q4_K_M.gguf",'type':"gguf",'prec':"4bit",'n_ctx':3072,"llm_param":-1},'seed':0}
#nllm_param = {'default_model':{'path':"allenai/OLMo-2-1124-7B-SFT",'type':"transformers",'prec':"16bit",'n_ctx':-1},'seed':0}
#nllm_param = {'default_model':{'path':"/llm/mistral-7b-instruct-v0.2.Q4_K_M.gguf",'type':"gguf",'prec':"4bit",'n_ctx':-1},'seed':0}
#mb_name = "test"
mb_name = "sanitize"
mb = MemoryBase.MemoryBase(mb_name,{"dslim/bert-base-NER":"ft",'all-MiniLM-L6-v2':"max"},{"context":{'all-MiniLM-L6-v2':1},"mixed":{'all-MiniLM-L6-v2':0.3,"dslim/bert-base-NER":0.7}})
nllm = NovelLLM.NovelLLM(nllm_param)
#"""
mb.create_embedding_table("Note",{"Title":"TEXT DEFAULT ''","Category":"TEXT DEFAULT ''"})
"""
for i in range(len(fantasy_snippets)):
	title = create_title(fantasy_snippets[i],nllm)
	category = create_category(fantasy_snippets[i],nllm)
	mb.add_embeddings("Note",fantasy_snippets[i],{"Title":title,"Category":category})
#"""

a = time.time()
#query_forced('Who is the best cook of all characters?',mb,nllm,history="",top_k=5,max_k=-1)
#query_forced('Who is the most experienced, brutal and merciless sadist? Explain in visual and gory detail.',mb,nllm,history="",top_k=5,max_k=-1)
mb.reindex_embeddings("Note",t=0,p=0)
sanitize_mb(mb,nllm,"Note",2)
b = time.time()
print("Time for generation: "+str(b-a))
#'''