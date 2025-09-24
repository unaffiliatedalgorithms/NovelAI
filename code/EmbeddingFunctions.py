import fasttext
import fasttext.util
from sentence_transformers import SentenceTransformer
# the longformer will perform some downloads before being run the first time
from transformers import LongformerModel, LongformerTokenizer
from transformers import AutoConfig
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import torch
import numpy as np
import os

class EmbedderSet():
	def __init__(self,models,weights):
		self.models = {}
		self.weights = weights
		self.dim = {}
		for key,value in models.items():
			self.models[key] = Embedder(value,key)
		for key,value in self.weights.items():
			self.dim[key] = 0
			for key2,value2 in value.items():
				self.dim[key]+=self.models[key2].dim
		
	def get_embeddings(self,text):
		raw_embeddings = {}
		embeddings = {}
		for key,value in self.models.items():
			raw_embeddings[key] = value.get_embedding(text)
		for key,value in self.weights.items():
			arrays = []
			for key2,value2 in value.items():
				arrays.append(value2*raw_embeddings[key2])
			embeddings[key] = np.concatenate(arrays)
		return embeddings
		

class Embedder():
	def __init__(self,type,name):
		self.type = type
		if(self.type=="ft"):
			current = os.getcwd()
			os.chdir("/llm")
			model_path = fasttext.util.download_model('en', if_exists='ignore')
			os.chdir(current)
			self.model = fasttext.load_model("/llm/"+model_path)
			self.dim = self.model.get_dimension()
			tokenizer = AutoTokenizer.from_pretrained(name,cache_dir="/llm")
			ner = AutoModelForTokenClassification.from_pretrained(name,cache_dir="/llm").to('cpu')
			self.nlp = pipeline("ner", model=ner, tokenizer=tokenizer,aggregation_strategy="simple",device="cpu")
			self.dim = self.model.get_dimension()
			self.ml = tokenizer.model_max_length
		elif(type=="long" or type=="long_max"):
			self.tokenizer = LongformerTokenizer.from_pretrained(name,cache_dir="/llm")
			self.model = LongformerModel.from_pretrained(name,cache_dir="/llm").to('cpu')
			self.dim = AutoConfig.from_pretrained(name,cache_dir="/llm").hidden_size
		else:
			self.model = SentenceTransformer(name,cache_folder="/llm",device='cpu')
			self.tokenizer = self.model.tokenizer
			self.ml = self.model.max_seq_length
			self.dim = self.model.get_sentence_embedding_dimension()
		
		
	
	# using a factor 2 of text length to see if max number of tokens is being overshot for windowing
	def get_embedding(self,text):
		if(self.type=="ft"):
			txt = ""
			if(len(text)*2<self.ml):
				entities = self.nlp(text)
				entities = [entity['word'] for entity in entities]
				txt = " ".join([name.replace(" ", "_") for name in entities])+" "+" ".join(entities)
			else:
				windows = sliding_window(text,self.ml,int(self.ml/20))
				for window in windows:
					entities = self.nlp(window)
					entities = [entity['word'] for entity in entities]
					txt+=" ".join([name.replace(" ", "_") for name in entities])+" "+" ".join(entities)
			embed = self.model.get_sentence_vector(txt)	
			#print(txt)
		elif(self.type=="long" or self.type=="long_max"):
			tokens = self.tokenizer(text, max_length=4096, truncation=True, return_tensors="pt")
			with torch.no_grad():
				outputs = self.model(**tokens)
			if(self.type=="long"):
				embed= torch.mean(outputs.last_hidden_state, dim=1).squeeze().cpu().numpy()
			else:
				embed= torch.max(outputs.last_hidden_state, dim=1)[0].squeeze().cpu().numpy()
		else:
			if(len(text)*2<self.ml):
				embed = self.model.encode(text)
			# text is too long. It will be broken into chunks using a sliding window approach
			else:
				windows = sliding_window(text,self.ml,int(self.ml/2))
				embeddings = self.model.encode(windows)
				if(self.type=="max"):
					embed = np.max(embeddings, axis=0)
				else:
					embed = np.sum(embeddings, axis=0)
		norm = np.linalg.norm(embed)
		return embed/norm if norm>0 else embed

def sliding_window(text, window_size=256, step=128):
    tokens = text.split()
    return [" ".join(tokens[i:i + window_size]) for i in range(0, len(tokens), step)]