import MemoryBase
import NovelLLM
import RecursiveQuery
import Algorithms
import time

def contradictory(text,background,ai):
	messages = [
			    {"role": "system", "content": """You're an AI tasked with evaluating if a text contains contradictory statements or logic. You are given the a text as well as a background text with additional comments which might resolve some contraditions. State if the text contains obvious contraditions in content or language, or there are parts where descriptions don't make sense or there are chronological inconsistencies. Process the text carefully. Answer only with "yes" or "no" and nothing else."""},
			    {"role": "user", "content": "Text:\n"+text+"\nBackground:\n"+background},
			    {"role": "system","content":""}
			]
	relevant = ai.instruct.chat(messages)
	if(relevant=="yes"):
		return True
	else:
		return False
		
def contradiction(text,background,ai):
	messages = [
			    {"role": "system", "content": """You're an AI tasked with finding the most obvious or glaring contradiction in a text. You are given a text which contains at least one contradiction or inconsistency in content, language, description, temporal setting, chronology or something else that doesn't make sense. You are also given a background text which might resolve some disparities. State the most glaring disparity or contradition which is not resolved in the background text and describe it."""},
			    {"role": "user", "content": "Text:\n"+text+"\nBackground:\n"+background},
			    {"role": "system","content":""}
			]
	return ai.instruct.chat(messages)
	
def contra2query(text,ai):
	messages = [
			    {"role": "system", "content": """You're an AI tasked with formulating a query to address contradictory statements. You are given the description of a contradiction that was found between an an established text and a new text. Formulate a query which clearly highlights the contrasting statements. The goal is to determine if the contradiction can be resolved with more context or if the new text is erroneous and needs to be adjusted. Your query will be checked against a collection of established statements to determine how to handle any contradictions.
			    Integrate any (one or multiple) of the following options based on your assessment of the best approach to address, and the nature the contradiction:
			    - Request further background information which could address the inconsistency. 
			    - Consider if chronology, point of view or similar could be relevant to resolving the contradiction.
			    - Verify the correctness/incorrectness of given statements
			    - Determine if the new text needs to be adjusted or corrected. 
			    
			    Keep all keywords in the query. Make sure the it is coherent and self-contained. Provide only the query and nothing else."""},
			    {"role": "user", "content": "Text:\n"+text},
			    {"role": "system","content":""}
			]
	return ai.instruct.chat(messages)
	
def resolution(query,answer,ai):
	messages = [
			    {"role": "system", "content": """You're an AI tasked with handling contradictions in between a new text and established texts from a database. Your are given a query which specifies and asks about the contradiction as well as a partial answer to resolve of the contradiction. Choose one of the following options:
			    "store": if the answer convincingly resolves all contradictions presented in the query and there are no implications the new text contains errors or requires modifications
			    "invent": if the contradiction is unresolved yet ambivalent and a resolution can be reasonably constructed with additional context (consider this if lacking chronology, point of view or other reasoning seems very likely to provide a resolution to the contradiction) and the answer doesn't propose any modifications to the new text
			    "fix": if the resolution of the contradiction would require convoluted or contrived reasoning; or the answer implies that any contradictions remain;or the answer proposes any modifications to the new text ; or targeted changes to wording or phrasing could resolve the contradiction
			    Choose one of the options "fix", "invent" or "store" and nothing else."""},
			    {"role": "user", "content": "Query:\n"+query+"\nAnswer:\n"+answer},
			    {"role": "system","content":""}
			]
	return ai.instruct.chat(messages)
	
def fix_guide(query,answer,ai):
	messages = [
			    {"role": "system", "content": """You're an AI tasked with removing contradictions from a text. You are given a query describing contradictions found in a text. You are also given an answer to the query. Define how to adapt any target text to remove the listed contradictions. Propose the removal or alteration of certain statements, redefining terms, adding explanations, etc. The final goal is to ensure the contradiction will be removed from any text. Proivde precise, targeted and instructive guidelines. The guidelines must be distinct and ensure that any texts will be corrected in the exact same way. Ensure the guildelines are coherent, self-contained and contain no references to the query or answer. Resolve the contradiction while keeping proposed changes to a minimum."""},
			    {"role": "user", "content": "Query:\n"+query+"\nPartial Answer:\n"+answer},
			    {"role": "system","content":""}
			]
	return ai.instruct.chat(messages)
	
def apply_fix(fix,text,ai):
	messages = [
			    {"role": "system", "content": """You're an AI tasked with removing contradictions from a text. You are given a guideline of what needs to be fixed and how, as well as a target text that needs fixing. Apply the guidelines to rewrite, improve or adjust the given text. Ensure careful and precise application of the guidelines. Provide only the fixed text without any comments as output."""},
			    {"role": "user", "content": "Guideline:\n"+fix+"\nText:\n"+text},
			    {"role": "system","content":""}
			]
	return ai.instruct.chat(messages)

def fix_relevant(fix,text,ai):
	messages = [
			    {"role": "system", "content": """You're an AI tasked with evaluating if a text contains any content which would be affected by a proposed correction. You are given a text and another text with proposed corrections to make. Answer if the text contains anything that would need to be changed based on any of the proposed corrections. Only propose making changes if these are neccessary to avoid contradictions within the text or with the proposed correction text. Answer only with "yes" or "no" and nothing else."""},
			    {"role": "user", "content": "Correction Text:\n"+fix+"\nText:\n"+text},
			    {"role": "system","content":""}
			]
	relevant = ai.instruct.chat(messages)
	if(relevant=="yes"):
		return True
	else:
		return False
		
def fix_mb(fix,mb,ai,table_name="Note",top_k=5,max_k=-1,expand=0.01):
	if(max_k<0):
		max_k = len(mb.embedders.weights)*-max_k
	# get the texts which are closest to the correction text
	matches = mb.similarity_search(table_name,fix,top_k,max_k*top_k)
	relevant = []
	for i in matches:
		relevant.append(fix_relevant(fix,i[1],ai))
	print("Current Correction:\n"+fix)	
	print("Matches relevant correction text")
	print(relevant)
	
	l = len(matches)
	r2 = relevant[int(l/2):]
	if(top_k<=l and expand>0 and expand<=sum(r2)/len(r2)):
		return fix_mb(question,mb,ai,table_name,top_k*2,max_k*2,expand)
	for i in range(len(matches)):
		if(relevant[i]):
			fixed = apply_fix(fix,matches[i][1],ai)
			fixed = RecursiveQuery.clean_text(fixed,ai)
			title = RecursiveQuery.create_title(fixed,ai)
			category = RecursiveQuery.create_category(fixed,ai)
			mb.update_embeddings(table_name,fixed,matches[i][0],{"Title":title,"Category":category})
			
def single_fix_loop(mb,ai,table_name="Note",top_k=5,max_k=-1,expand=0.01):
	
	ids = mb.get_all_id(table_name)
	ids = Algorithms.dl_dict(ids)
	while(ids.len>0):
		id = ids.head
		print("Current Index for correction: "+str(id))
		f = mb.get_fields(table_name,id,["embedding_text"])
		text = f[0]
		if(remove_contradictions(text,mb,ai,table_name=table_name,top_k=top_k,max_k=max_k,expand=expand)):
			ids.delete(id)
			
def related_content(text1,text2,ai):
	messages = [
			    {"role": "system", "content": """You're an AI tasked with evaluating if two texts share common proper nouns or similar unique words. You are given two texts and need to determine if there are any proper nouns or other words that refer to a unique entity, object or situation that are present in both. Answer with "yes" or "no" and nothing else."""},
			    {"role": "user", "content": "First Text:\n"+text1+"\nSecond Text:\n"+text2},
			    {"role": "system","content":""}
			]
	relevant = ai.instruct.chat(messages)
	if(relevant=="yes"):
		return True
	else:
		return False
		
def conflicting(text1,text2,background,ai):
	messages = [
			    {"role": "system", "content": """You are an AI evaluating whether two texts contain contradictory statements. You are provided with two texts and a background text that might resolve apparent contradictions.
Identify whether any statements in one text clearly contradict statements in the other based on character, adjectives, actions, temporal settings, chronology, logical consistency, or anything else.  Ignore contradictions that are resolved by the background text. If contradictions remain after evaluating the background text, respond "yes." If all contradictions are resolved by the background text, respond "no." Provide only "yes" or "no" as your response and nothing else."""},
			    {"role": "user", "content": "First Text:\n"+text1+"\nSecond Text:\n"+text2+"\nBackground Text:\n"+background},
			    {"role": "system","content":""}
			]
	relevant = ai.instruct.chat(messages)
	if(relevant=="yes"):
		return True
	else:
		return False
		
def find_conflict(text1,text2,background,ai):
	messages = [
			    {"role": "system", "content": """You are an AI tasked with identifying the most prominent unresolved contradiction between or within two texts. You are given a new text, an established text, and a background text. There are contradictions between the new text and the established text, some of which might be resolved by the background text. Your task is to find the most obvious contradiction that remains unresolved despite the background text.
Identify contradictions in character, adjectives, actions, temporal settings, chronology, logical consistency or anything else. Ignore contradictions that are resolved by the background text. Carefully asses and select the most prominent contradiction that remains unresolved. Describe the contradiction clearly and concisely, in a self-contained manner."""},
			    {"role": "user", "content": "New Text:\n"+text1+"\nEstablished Text:\n"+text2+"\nBackground Text:\n"+background},
			    {"role": "system","content":""}
			]
	return ai.instruct.chat(messages)
	
def invent_query(query,answer,ai):
	messages = [
			    {"role": "system", "content": """You are an AI tasked with reasoning how contradictory statements in a text can be resolved through extended reasoning. You are given a query which asks about the contradiction and a reply to that query. Your goal is to create a new query which focuses on gathering more information to resolve the contradiction presented in the initial query. Make sure the query is coherent, well-structured and self-contained. Provide only the query and nothing else."""},
			    {"role": "user", "content": "Contradiction Query:\n"+query+"\nReply:\n"+answer},
			    {"role": "system","content":""}
			]
	return ai.instruct.chat(messages)
		
		
# I expect text consistency errors to appear at here at some time
# also there will likely be issues that the list of matches will be updated if the memorybase is sanitized during the loop
def find_error(text,mb,ai,table_name="Note",top_k=5,max_k=-1,expand=0.2,nquer=[3,4]):
	if(max_k<0):
		max_k = len(mb.embedders.weights)*-max_k*top_k
	# get the texts which are closest to the correction text
	matches = mb.similarity_search(table_name,text,top_k,top_k*max_k)
	relevant = []
	for i in matches:
		relevant.append(related_content(text,i[1],ai))
	print("Text are related to initial text")
	print(relevant)
	
	l = len(matches)
	r2 = relevant[int(l/2):]
	if(top_k<=l and expand>0 and expand<=sum(r2)/len(r2)):
		return find_error(text,mb,ai,table_name,top_k*2,max_k*2,expand)
	for i in range(len(matches)):
		if(relevant[i]):
			background = ""
			while(conflicting(text,matches[i][1],background,ai)):
				print("\nContradiction found:\n")
				print("Inserting text:")
				print(text)
				print("MB text:")
				print(matches[i][1])
				print("Background text:")
				print(background)
				conf = find_conflict(text,matches[i][1],background,ai)
				print("Conflict:")
				print(conf)
				query = contra2query(conf,ai)
				print("Conflict Query:")
				print(query)
				answer = RecursiveQuery.query(query,mb,ai,table_name)
				print("Query Answer:")
				print(answer)
				solution = resolution(query,answer,ai)
				print("Approach:")
				print(solution)
				if(solution=="store"):
					note = RecursiveQuery.query2note(query,answer,ai)
					RecursiveQuery.merge2db(note,mb,ai,table_name)
					background = RecursiveQuery.merge_texts(background,note,ai)
				elif(solution=="invent"):
					history = ""
					background = RecursiveQuery.merge_texts(background,answer,ai)
					query = invent_query(query,answer,ai)
					("Inventing Query:")
					print(query)
					("Query Answer:")
					answer = RecursiveQuery.query_forced(query,mb,ai,table_name,history,nquer=nquer,fquer=nquer)
					print(answer)
					background = RecursiveQuery.merge_texts(background,answer,ai)
				else:
					fix = fix_guide(query,answer,ai)
					print("Fix Guide:")
					print(fix)
					fixed = apply_fix(fix,text,ai)
					text = RecursiveQuery.clean_text(fixed,ai)
					text = find_error(text,mb,ai,table_name,top_k,max_k,expand,nquer=nquer)
					return text
	return text
				
	

#def merge_resolutions(background,note,)
	
'''
nllm_param = {'default_model':{'path':"/llm/Replete-LLM-V2.5-Qwen-32b-Q4_K_M.gguf",'type':"gguf",'prec':"4bit",'n_ctx':3072,"llm_param":-1},'seed':0}
mb_name = "sanitize"
mb = MemoryBase.MemoryBase(mb_name,{"dslim/bert-base-NER":"ft",'all-MiniLM-L6-v2':"max"},{"context":{'all-MiniLM-L6-v2':1},"mixed":{'all-MiniLM-L6-v2':0.6,"dslim/bert-base-NER":0.4}})
nllm = NovelLLM.NovelLLM(nllm_param)
mb.create_embedding_table("Note",{"Title":"TEXT DEFAULT ''","Category":"TEXT DEFAULT ''"})
text = """Windmere is a city under water. In the markets of Windmere the the birdman Callidus often plays melacholic songs on his lute.
"""
find_error(text,mb,nllm,"Note")
#'''