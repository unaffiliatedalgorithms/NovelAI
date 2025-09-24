from transformers import AutoModelForCausalLM, AutoTokenizer,set_seed
from llama_cpp import Llama
from transformers import BitsAndBytesConfig
import torch,time,numpy,copy

def llm_parameters(max_new_tokens=-1,temperature=1,do_sample=True,top_k=50,top_p=1,num_beams=1,num_beam_groups=1):
	return {"max_new_tokens":max_new_tokens,"temperature":temperature,"do_sample":do_sample,"top_k":top_k,"top_p":top_p,"num_beams":num_beams,"num_beam_groups":num_beam_groups}
def nllm_parameters(default_model,writing_model={},instruct_model={},query_model={},verifier_model={},seed=-1):
	return {"default_model":default_model,"writing_model":writing_model,"instruct_model":instruct_model,"seed":seed}
n_ctx = 4096


class NovelLLM:
	def __init__(self,param):
		self.seed = param["seed"]
		if(self.seed<0):
			self.seed = numpy.random.randint(0, 2**32)
		torch.manual_seed(self.seed)
		set_seed(self.seed)
		self.default = LLM(param['default_model']['path'],param['default_model']['type'],param['default_model']['prec'],param['default_model']['n_ctx'],param['default_model']['llm_param'])
		if('writing_model' in param):
			self.writer = LLM(param['writing_model']['path'],param['writing_model']['type'],param['writing_model']['prec'],param['writing_model']['n_ctx'],param['writing_model']['llm_param'])
		else:
			self.writer=self.default
		if('instruct_model' in param):
			self.instruct = LLM(param['instruct_model']['path'],param['instruct_model']['type'],param['instruct_model']['prec'],param['instruct_model']['n_ctx'],param['instruct_model']['llm_param'])
		else:
			self.instruct=self.default
	
	# extract all proper names from a given text
	def extract_pn(self,text,llm_param=-1):
		if(llm_param==-1):
			llm_param = self.llm_parameters
		messages = [
			    {"role": "system", "content": """Your are an AI specialized in extracting proper names. When provided a text you extract all proper nouns found in the text as and provide them as a list of unique comma separated words and nothing else.
			    """},
			    {"role": "user", "content": """Extract all proper names (such as names of people, places, organizations, and fantasy creatures like "goblin" or "mermaid") from the text. Ensure that multi-word names (e.g., "The One Ring", "Mount Doom") and possessive forms (e.g., "Ogar's mother") are included correctly. Proper names may include definite articles, descriptive words, and fantasy terms. Provide the extracted names as a unique, comma-separated list, maintaining correct capitalization. Do not include duplicates or any other words. \nText:"""+text},
			    {"role": "system","content":""}
			]
		proper_names =  self.instruct.chat(messages,param=llm_param).split(",")
		return [s.strip() for s in proper_names]
	
	def split2sections(self,text,number=5,separator="---",llm_param=-1):
		messages = [
			    {"role": "system", "content": """You're are an AI specialized in splitting text in the appropriate spots. You will be given a text that you should split into a specific number of sections with a prescribed separator sequence between sections. Preserve the orginal text content during this operation."""},
			    {"role": "user", "content": "Number of sections: "+str(number)+"\nSeparator sequence:\n"+separator+"\nText:\n"+text},
			    {"role": "system","content":""}
			]
		return self.instruct.chat(messages,param=llm_param)
	
	def split2questions(self,text,separator="---",llm_param=-1):
		messages = [
			    {"role": "system", "content": """You're are an AI specialized in splitting text in the appropriate spots. You are be given a text of questions. Split the text into individual questions using the prescribed separator sequence. Preserve the orginal text content during this operation.
			    """},
			    {"role": "user", "content": "Separator Sequence:"+separator+"\nText:\n"+text},
			    {"role": "system","content":""}
			]
		return self.instruct.chat(messages,param=llm_param)
		
	def split2list(self,text,separator="---"):
		texts = [t.lstrip() for t in text.split(separator)]
		# remove spurious texts from question list. These texts are likely to vary based on LLM model
		texts = [x for x in texts if x not in ["","</s>","</span>"]]
		return texts
		

class LLM:
	def __init__(self,modelname,model_type,precision,n_ctx,llm_param=-1):
		if(llm_param==-1):
			self.llm_parameters = copy.deepcopy(llm_parameters())
		else:
			self.llm_parameters = copy.deepcopy(llm_param)
		nf8_config = BitsAndBytesConfig(
			load_in_8bit=True,
			bnb_8bit_quant_type="nf8",
			bnb_8bit_use_double_quant=True,
			bnb_8bit_compute_dtype=torch.bfloat16
		)
		nf4_config = BitsAndBytesConfig(
			load_in_4bit=True,
			bnb_4bit_quant_type="nf4",
			bnb_4bit_use_double_quant=True,
			bnb_4bit_compute_dtype=torch.bfloat16
		)
		self.model_type = model_type
		if(model_type=="transformers"):
			print("Using Transformers to load or download model")
			if(precision=="4bit"):
				self.model = AutoModelForCausalLM.from_pretrained(modelname,quantization_config=nf4_config,cache_dir="/llm",device_map="auto")
			elif(precision=="8bit"):
				self.model = AutoModelForCausalLM.from_pretrained(modelname,lquantization_config=nf8_config,cache_dir="/llm",device_map="auto")
			elif(precision=="16bit"):
				self.model = AutoModelForCausalLM.from_pretrained(modelname,torch_dtype="float16",cache_dir="/llm",device_map="auto")
			else:
				print("Loading model with full (32bit?) precision.")
				self.model = AutoModelForCausalLM.from_pretrained(modelname,cache_dir="/llm",device_map="auto")
			self.tokenizer = AutoTokenizer.from_pretrained(modelname,cache_dir="/llm")

		elif(model_type=="gguf"):
			print("Using Llama-cpp to load gguf model")
			verbose = False
			if(n_ctx<=0):
				self.model = Llama(model_path=modelname,n_gpu_layers=-1,logits_all=False,verbose=verbose)
			else:
				self.model = Llama(model_path=modelname,n_gpu_layers=-1,logits_all=False,n_ctx=n_ctx,verbose=verbose)
		else:
			print("Invalid model type selection. Currently options are loading gguf packaged (\"gguf\"), or hugging face models using the transformers library (\"transformers\")")
			
	def chat(self,messages,param=-1):
		if (param==-1):
			param = self.llm_parameters
		if(self.model_type=="transformers"):
			inputs = self.tokenizer.apply_chat_template(messages,return_tensors='pt',return_token_type_ids=False)
			inputs = inputs.to("cuda")
			maxnt = param["max_new_tokens"]
			if(maxnt==-1):
				maxnt= self.model.config.max_position_embeddings
			response = self.model.generate(inputs, max_new_tokens=maxnt , do_sample=param["do_sample"] , top_k=param["top_k"] , top_p=param["top_p"],num_beams=param["num_beams"],num_beam_groups=param["num_beam_groups"],temperature=param["temperature"])
			return self.tokenizer.decode(response[0,inputs.shape[-1]:], skip_special_tokens=True)
		elif(self.model_type=="gguf"):
			maxnt = param["max_new_tokens"]
			if(maxnt==-1):
				#maxnt = self.model.context_params.n_ctx
				pass
			response = self.model.create_chat_completion(messages, max_tokens=maxnt, top_k=param["top_k"], top_p=param["top_p"],temperature=param["temperature"])
			return response["choices"][0]["message"]["content"]
	
	def generate(self,text,param=-1):
		if (param==-1):
			param = self.llm_parameters
		if(self.model_type=="transformers"):
			inputs = self.tokenizer(text,return_tensors='pt',return_token_type_ids=False)
			# making sure the input text is on the GPU
			inputs = inputs.to("cuda")
			maxnt = param["max_new_tokens"]
			if(maxnt==-1):
				maxnt = self.model.config.max_position_embeddings
			response = self.model.generate(**inputs, max_new_tokens=maxnt, do_sample=param["do_sample"] , top_k=param["top_k"] , top_p=param["top_p"],num_beams=param["num_beams"],num_beam_groups=param["num_beam_groups"],temperature=param["temperature"])
			return self.tokenizer.decode(response[0,inputs.input_ids.size(1):], skip_special_tokens=True),self.tokenizer.batch_decode(response, skip_special_tokens=True)[0]
		elif(self.model_type=="gguf"):
			max_new_tokens = param["max_new_tokens"]
			if(max_new_tokens==-1):
				pass
			response = self.model(text, max_tokens=max_new_tokens, top_k=param["top_k"], top_p=param["top_p"],temperature=param["temperature"])["choices"][0]["text"]
			return response,text+response