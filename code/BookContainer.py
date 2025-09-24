import NovelLLM as nl
import DBManager as db
import VectorBase  as vb

def default_text_param(summary,title="",genre="",style="",notes=[]):
	return {"summary":summary,"title":title,"genre":genre,"notes"=notes}
def default_nllm_param(param):
	return 0
	
class BookContainer():
	def __init__(self,text_param,nllm_param,vb_param,db_path):
		self.summary = summary
		self.ai = nl.NovelLLM(nllm_param)
		self.db = db.BookDB(db_path)
		self.vb = vb.VectorBase(vb_param['model_types'],vb_param['dim'])
		
	def blank(self):
		if(genre!=""):
			self.genre = genre
		else:
			messages = [
			    {"role": "system", "content": """You are an AI assistant specialized in generating concise, creative, and fitting genres for books based on text summaries. 
			    Whenever a summary is provided, respond with a compact comma seperated set of appropriate genres. Answer ONLY with the list of genre names and nothing else.
			    """},
			    {"role": "user", "content": "Provide fitting genre(s) for this summary text:\n"+summary},
			    {"role": "system","content":""}
			]
			self.genre = self.AI.writer.chat(messages)
		if(style!=""):
			self.style = style
		else:
			messages = [
			    {"role": "system", "content": """You are an AI writing expert specializing in analyzing and describing writing styles. When provided with a text summary your task is to craft a detailed paragraph describing the intended writing style for the expanded text. Include examples of tone, sentence structure, pacing, and vocabulary where applicable. Tailor the description to meet the user's preferences if they specify a particular tone (e.g., formal, conversational, academic, or poetic). Ensure your style descriptions are clear and detailed enough for an experienced writer to understand and replicate. Keep the descriptive structured and concise.
			    """},
			    {"role": "user", "content": "Provide a fitting style for this summary text. The genre is"+self.genre+"\n"+summary},
			    {"role": "system","content":""}
			]
			self.style = self.ai.writer.chat(messages)
		# Define the path for the database
		db_path = '/book/database/new_database.db'
		self.memory = mb.MemoryBase(db_path,self.AI)
		
	

summary = """Shelter

Shelter tells the story of Rin, a 17-year-old girl who lives her life inside of a futuristic simulation completely by herself in infinite, beautiful loneliness. Each day, Rin awakens in virtual reality and uses a tablet which controls the simulation to create a new, different, beautiful world for herself. Until one day, everything changes, and Rin comes to learn the true origins behind her life inside a simulation. 
Rin gradually remembers her life on earth with her father. Her father raised her on his own best he could after the passing of her mother. During this time a moon sized planetoid approaches the earth spelling the earth's imminent destruction. Rin's father continues to be the best father he can while preparing a space ship to send Rin away from earth. He puts her into a virtual reality environment and leaves her a message for when she is mature enough to understand why he did what he did for her and hopes that despite being alone that she can overcome this."""

#llm = {'path':"allenai/OLMo-2-1124-7B-SFT",'type':"transformers",'prec':"16bit"}
llm = {'path':"/llm/Replete-LLM-V2.5-Qwen-32b-Q4_K_M.gguf",'type':"gguf",'prec':"4bit"}
#llm = {'path':"/llm/mistral-7b-instruct-v0.2.Q4_K_M.gguf",'type':"gguf",'prec':"4bit"}
AI = nl.NovelLLM(llm,seed=0)
book = BookContainer(AI,summary)
print("Genre(s): "+book.genre+"\n")
print("Style: "+book.style+"\n")
#print(book.extract_pn("""
#Carry the burden of the One Ring(TM) with Pop! Frodo Baggins! This hobbit(TM) is looking to find his next adventure in your The Lord of the Rings(TM) collection as this exclusive Pop! Frodo Baggins with Orc Helmet! Vinyl figure is approximately 3.7-inches tall.
#"""))
