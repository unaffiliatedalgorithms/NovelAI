import MemoryBase
import NovelLLM
import RecursiveQuery
import Refinement
import time

class HierarchicalWriter():
	def __init__(self,mb,ai,summary="",genre="",guide="",style="",technical=""):
		self.mb = mb
		self.ai = ai
		self.create_hierarchy_table()
		
		
	def create_hierarchy_table(self):
		mb.create_embedding_table("Hierarchy",{"Title":"TEXT DEFAULT ''","Parent":"INTEGER DEFAULT -1","Previous":"INTEGER DEFAULT -1","Next":"INTEGER DEFAULT -1","Children":"FLOAT8[] DEFAULT ARRAY[]::FLOAT8[]","Depth":"INTEGER"})
		
	def expand_summary(self,text):
		pass
		
	def narrative_element(self,overview,depth,type,embedding="",top_k=5,max_k=-1,expand=0.3,nquer=[3,4],fquer=[3,4]):
		questions = self.question_generator(overview,depth,type,embedding,number=6,separator="---")
		print(questions)
		text = ""
		for q in questions:
			answer = RecursiveQuery.query_forced(q,self.mb,self.ai,table_name="Note",history="",top_k=top_k,max_k=max_k,expand=expand,nquer=nquer,fquer=fquer)
			print(q)
			print(answer)
			text = self.expand_answer(q,answer,overview,text,type)
			print(text)
		return text
		
	def expand_answer(self,query,answer,overview,beginning,type):
		start = """Your are an AI writing assistant. Your task is to generate a text for a narrative structure element of the text. Focus on the """
		end = """of the text. You are given a overview of the narrative, a question and answer pair relative to the narrative structure element and the beginning of your target text. Integrate the information from the question-answer pair into the beginning text. Structure the text in the manner a professional author would to highlight and present the narrative element.
			"""
		intermediate = ""
		match type:
			case "motivation":
				intermediate = """purpose, motivation, or core motivation of """
			case "characters":
				intermediate = """characters and their roles and dynamics in """
			case "mood":
				intermediate = """mood and tone of """
			case "sequence":
				intermediate = """narrative sequence of """
			case "chronology":
				intermediate = """chronology of events of """
			case "imagery":
				intermediate = """imagery (all senses) and setting of """
			case "conclusion":
				intermediate = """conclusion and consequences of """
		message = [
			    {"role": "system", "content": start+intermediate+end},
			    {"role": "user", "content": "Beginning:\n"+beginning+"\nOverview:\n"+overview+"\nQuestion:\n"+query+"\nAnswer:\n"+answer},
			    {"role": "system","content":""}
			]
		return self.ai.instruct.chat(message)
		
	def question_generator(self,text,depth,type,embedding="",number=6,separator="---",llm_param=-1):
		messages = []
		start = """Your are an AI writing assistant. You are given a summary text and its embedding within the narrative of a novel. Your task is to generate clarifying questions that will help """
		end = """the summary text. You have no prior knowledge beyond the provided summary and its embedding in a narrative hierarchy. The depth value of each narrative embedding indicates how many embeddings it is away from the finalized written text (layer 0). Your questions should focus on clarifying ambiguities, unknown names, places, or concepts. Do not include explanations, assumptions, or any additional output.
			"""
		intermediate = ""
		match type:
			case "motivation":
				intermediate = """determine the purpose, motivation, or core motivation of """
			case "characters":
				intermediate = """determine the characters and their roles and dynamics in """
			case "mood":
				intermediate = """determine the mood and tone of """
			case "sequence":
				intermediate = """create the narrative sequence of """
			case "chronology":
				intermediate = """create the chronology of events of """
			case "imagery":
				intermediate = """create the imagery (all senses) and setting of """
			case "conclusion":
				intermediate = """create the conclusion and consequences of """
		messages = [
				{"role": "system", "content": start+intermediate+end},
				{"role": "user", "content": "Generate"+str(number)+"clarifying questions. \n Use the following to separator sequence between questions:"+separator+"\nCurrent depth:"+str(depth)+"\nSummary:\n"+text+"\nEmbedding:"+embedding},
				{"role": "system","content":""}
			]
		question_list = self.ai.instruct.chat(messages)
		return self.ai.split2list(question_list,separator)
		
	def summary2timeline(self,text,number=5,separator="---",llm_param=-1):
		messages = [
			    {"role": "system", "content": """Your are an AI specialized in . You will be given a text that you should split into a certain number of sections with a prescribed separator sequence. Preserve the orginal text content during this operation.
			    """},
			    {"role": "user", "content": "Split the following text into"+str(number)+"sections. \n Use the following to separator sequence:\n"+separator+"\nText:\n"+text},
			    {"role": "system","content":""}
			]
			
			
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
summary = """In the kingdom of Eldoria, the dark sorcerer Vaelgor seeks the lost relic of Zyphoros, a powerful artifact hidden in the ruins of Arkanvale. As his Shadow Horde rises, warriors, scholars, and rogues from across the land unite to stop him. Altharion, a mighty warrior wielding the cursed sword Nightfang, leads the fight, while Prince Kaelen and his wyvern Valdris search for an ancient prophecy. Meanwhile, assassins, mages, and rulers--each with their own motives--maneuver through a world on the brink of chaos. As alliances form and betrayals unfold, the fate of Eldoria hangs in the balance, with the relic holding the power to shape the world's destiny."""


nllm_param = {'default_model':{'path':"/llm/Replete-LLM-V2.5-Qwen-32b-Q4_K_M.gguf",'type':"gguf",'prec':"4bit",'n_ctx':3072,"llm_param":-1},'seed':0}
#nllm_param = {'default_model':{'path':"allenai/OLMo-2-1124-7B-SFT",'type':"transformers",'prec':"16bit",'n_ctx':-1},'seed':0}
#nllm_param = {'default_model':{'path':"/llm/mistral-7b-instruct-v0.2.Q4_K_M.gguf",'type':"gguf",'prec':"4bit",'n_ctx':-1},'seed':0}
mb_name = "test"
#mb_name = "sanitize"
mb = MemoryBase.MemoryBase(mb_name,{"dslim/bert-base-NER":"ft",'all-MiniLM-L6-v2':"max"},{"context":{'all-MiniLM-L6-v2':1},"mixed":{'all-MiniLM-L6-v2':0.3,"dslim/bert-base-NER":0.7}})
nllm = NovelLLM.NovelLLM(nllm_param)
#"""
mb.create_embedding_table("Note",{"Title":"TEXT DEFAULT ''","Category":"TEXT DEFAULT ''"})
h = HierarchicalWriter(mb,nllm)
#"""
for i in range(len(fantasy_snippets)):
	title = RecursiveQuery.create_title(fantasy_snippets[i],nllm)
	category = RecursiveQuery.create_category(fantasy_snippets[i],nllm)
	mb.add_embeddings("Note",fantasy_snippets[i],{"Title":title,"Category":category})
#"""

a = time.time()
h.narrative_element(summary,3,"motivation")
b = time.time()
print("Time for generation: "+str(b-a))
#'''