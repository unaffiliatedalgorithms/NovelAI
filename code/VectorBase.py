import faiss
import fasttext
import fasttext.util
from sentence_transformers import SentenceTransformer
# the longformer will perform some downloads before being run the first time
from transformers import LongformerModel, LongformerTokenizer
from transformers import AutoConfig
import torch
import numpy as np
import os


class VectorBase:
	def __init__(self,model_types,dim=32):
		# Create schema
		schema = MilvusClient.create_schema(
			auto_id=False,
			enable_dynamic_field=True,
		)
		fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=50, is_partition_key=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128)
]
			
	def add_text(self,text,id):
		for i in range(len(self.models)):
			embed = self.models[i].get_embedding(text)
			self.db[i].add(np.expand_dims(embed, axis=0))
			D, I = self.db[i].search(np.expand_dims(embed, axis=0),1)
			self.index[i][I[0][0]] = id
			
	def remove_text(self,text):
		for i in range(len(self.models)):
			embed = self.models[i].get_embedding(text)
			D, I = self.db[i].search(np.expand_dims(embed, axis=0),1)
			self.db[i].remove_ids(np.array([I[0][0]], dtype='int64'))
			del self.index[i][I[0][0]]
	
	def search(self,query,top_k=5,max_k = 10):
		top = []
		dist = []
		for i in range(len(self.models)):
			query_vector = np.expand_dims(self.models[i].get_embedding(query), axis=0)
			distances,indices = self.db[i].search(query_vector,top_k)
			top.append(indices[0])
		unique_indices = [] 
		for i in range(len(top[0])):
			for j in range(len(top)):
				unique_indices.append(self.index[j][top[j][i]])
		return list(dict.fromkeys(unique_indices))[:max_k]
		
class Embedder:
	def __init__(self,type,name):
		self.type = type
		if(type=="ft"):
			current = os.getcwd()
			os.chdir("/llm")
			model_path = fasttext.util.download_model('en', if_exists='ignore')
			os.chdir(current)
			self.model = fasttext.load_model("/llm/"+model_path)
			self.dim = self.model.get_dimension()
		elif(type=="long" or type=="long_max"):
			self.tokenizer = LongformerTokenizer.from_pretrained(name,cache_dir="/llm")
			self.model = LongformerModel.from_pretrained(name,cache_dir="/llm").to('cpu')
			self.dim = AutoConfig.from_pretrained(name,cache_dir="/llm").hidden_size
		else:
			self.model = SentenceTransformer(name,cache_folder="/llm",device='cpu')
			self.tokenizer = self.model.tokenizer
			self.ml = self.model.max_seq_length
			self.dim = self.model.get_sentence_embedding_dimension()
	
	def get_embedding(self,text):
		if(self.type=="ft"):
			embed = self.model.get_sentence_vector(text)
		elif(self.type=="long" or self.type=="long_max"):
			tokens = self.tokenizer(text, max_length=4096, truncation=True, return_tensors="pt")
			with torch.no_grad():
				outputs = self.model(**tokens)
			if(self.type=="long"):
				embed= torch.mean(outputs.last_hidden_state, dim=1).squeeze().cpu().numpy()
			else:
				embed= torch.max(outputs.last_hidden_state, dim=1)[0].squeeze().cpu().numpy()
		else:
			tokens = self.tokenizer.encode(text)
			num_tokens = len(tokens)
			if(num_tokens<self.ml):
				embed = self.model.encode(text)
			# text is too long. It will be broken into chunks using a sliding window approach
			else:
				windows = sliding_window(text,self.ml,int(self.ml/2))
				embeddings = self.model.encode(windows)
				if(self.type=="max"):
					embed = np.max(embeddings, axis=0)
				else:
					embed = np.sum(embeddings, axis=0)
		return embed/np.linalg.norm(embed)
		
def sliding_window(text, window_size=256, step=128):
    tokens = text.split()
    return [" ".join(tokens[i:i + window_size]) for i in range(0, len(tokens), step)]