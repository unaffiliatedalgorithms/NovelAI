import EmbeddingFunctions
import psycopg2


# memory base is a vector database with embedding functions etc.
# This serves as an abstract of general databases of this type
class MemoryBase():
	def __init__(self,dbname,models,weights,dbparam={"M":16,"ef_construction":200}):
		self.name = dbname
		self.dbparam = dbparam
		conn = psycopg2.connect(dbname="postgres")
		conn.autocommit = True
		cursor = conn.cursor()
		cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (self.name,))
		if cursor.fetchone():
			print(f"Database '{self.name}' already exists.")
		else:
			cursor.execute(f"CREATE DATABASE {self.name}")
		cursor.close()
		conn.close()
		conn = self.conn()
		conn.autocommit = True
		cursor = conn.cursor()
		cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
		cursor.close()
		conn.close()
		self.embedders = EmbeddingFunctions.EmbedderSet(models,weights)
		self.setup()
		self.index_counters = {}
	
	# implement in subclass
	def setup(self):
		pass
	
	def conn(self):
		return psycopg2.connect(f"dbname={self.name}")
	
	def create_embedding_table(self,table_name,misc={}):
		command = f"CREATE TABLE IF NOT EXISTS {table_name} (Id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, embedding_text TEXT NOT NULL"
		command+="".join([f", {key}_embedding VECTOR({self.embedders.dim[key]})" for key in self.embedders.weights.keys()])
		command+="".join([f", {key} {value}" for key,value in misc.items()])
		command+=");"
		conn = self.conn()
		cursor = conn.cursor()
		cursor.execute(command)
		for key,value in self.embedders.weights.items():
			cursor.execute(f"DROP INDEX IF EXISTS {table_name}_{key}_embedding_idx;")
			cursor.execute(f"CREATE INDEX {table_name}_{key}_embedding_idx ON {table_name} USING hnsw ({key}_embedding vector_cosine_ops) WITH (M={self.dbparam["M"]}, ef_construction={self.dbparam["ef_construction"]});")
		conn.commit()
		cursor.close()
		conn.close()
		if(table_name not in self.index_counters):
			self.index_counters[table_name]={"deletions":0,"additions":0,"size":0}
			self.index_counters[table_name]["size"] = self.get_num_rows(table_name)
	
	def add_embeddings(self,table_name,text,misc={}):
		if(table_name not in self.index_counters):
			if(table_name not in self.index_counters):
				self.index_counters[table_name]={"deletions":0,"additions":0,"size":0}
				self.index_counters[table_name]["size"] = self.get_num_rows(table_name)
		self.index_counters[table_name]["additions"]+=1
		self.index_counters[table_name]["size"]+=1
		pre = "".join([f"{key}: {value}\n" for key,value in misc.items()])
		embeddings = self.embedders.get_embeddings(pre+text)
		command = f"INSERT INTO {table_name} (embedding_text"
		command+="".join([f", {key}_embedding" for key in embeddings.keys()])
		command+="".join([f", {key}" for key in misc.keys()])
		command+=") VALUES (%s"
		command+="".join([", %s" for key in embeddings.keys()])
		command+="".join([", %s" for key in misc.keys()])
		command+=") RETURNING Id;"
		conn = self.conn()
		cursor = conn.cursor()
		cursor.execute(command,(text,)+tuple([x.tolist() for x in embeddings.values()])+tuple(misc.values()))
		last_inserted_id = cursor.fetchone()[0]
		conn.commit()
		cursor.close()
		conn.close()
		return last_inserted_id
		
	def batch_add_embeddings(self,table_name,texts,misc={}):
		id = []
		for text in texts:
			id=self.add_embeddings(table_name,text,misc)
		return id
		
	def update_embeddings(self,table_name,text,id,misc={}):
		if(table_name not in self.index_counters):
			self.index_counters[table_name]={"deletions":0,"additions":0,"size":0}
			self.index_counters[table_name]["size"] = self.get_num_rows(table_name)
		self.index_counters[table_name]["additions"]+=1
		self.index_counters[table_name]["deletions"]+=1
		pre = [f"{key}: {value}\n" for key,value in misc.items()]
		pre = "".join(pre)
		embeddings = self.embedders.get_embeddings(pre+text)
		command = f"UPDATE {table_name} SET embedding_text=%s"
		command+="".join([f", {key}_embedding=%s" for key in embeddings.keys()])
		command+="".join([f", {key}=%s" for key in misc.keys()])
		command+=f" WHERE Id = {id};"
		conn = self.conn()
		cursor = conn.cursor()
		cursor.execute(command,(text,)+tuple([x.tolist() for x in embeddings.values()])+tuple(misc.values()))
		conn.commit()
		cursor.close()
		conn.close()
		
	def get_fields(self,table_name,id,misc):
		command = "SELECT "+", ".join(misc)+ f" FROM {table_name} WHERE Id={id};"
		conn = self.conn()
		cursor = conn.cursor()
		cursor.execute(command)
		row = cursor.fetchone()
		conn.commit()
		cursor.close()
		conn.close()
		return row
		
	def update_fields(self,table_name,id,misc):
		command = f"UPDATE {table_name} SET "+",".join([str(key)+"=%s" for key in misc.keys()])
		command+=f" WHERE Id = {id};"
		conn = self.conn()
		cursor = conn.cursor()
		cursor.execute(command,tuple(misc.values()))
		conn.commit()
		cursor.close()
		conn.close()
		
	def delete_row(self,table_name,id):
		if(table_name not in self.index_counters):
			self.index_counters[table_name]={"deletions":0,"additions":0,"size":0}
			self.index_counters[table_name]["size"] = self.get_num_rows(table_name)
		self.index_counters[table_name]["size"]-=1
		self.index_counters[table_name]["deletions"]+=1
		command = f"DELETE FROM {table_name} WHERE Id = {id};"
		conn = self.conn()
		cursor = conn.cursor()
		cursor.execute(command)
		conn.commit()
		cursor.close()
		conn.close()
		
	def reindex_embeddings(self,table_name,t=1000,p=0.15):
		if(table_name not in self.index_counters):
			self.index_counters[table_name]={"deletions":0,"additions":0,"size":0}
			self.index_counters[table_name]["size"] = self.get_num_rows(table_name)
		if(self.index_counters[table_name]["size"]>=t and (self.index_counters[table_name]["deletions"]+self.index_counters[table_name]["deletions"])/self.index_counters[table_name]["size"]>=p):
			self.index_counters[table_name]["deletions"] = 0
			self.index_counters[table_name]["additions"] = 0
			conn = self.conn()
			cursor = conn.cursor()
			for key,value in self.embedders.weights.items():
				cursor.execute(f"DROP INDEX IF EXISTS {table_name}_{key}_embedding_idx;")
				cursor.execute(f"CREATE INDEX {table_name}_{key}_embedding_idx ON {table_name} USING hnsw ({key}_embedding vector_cosine_ops) WITH (M={self.dbparam["M"]}, ef_construction={self.dbparam["ef_construction"]});")
			conn.commit()
			cursor.close()
			conn.close()
			
	def vacuum_table(self,table_name):
		conn = self.conn()
		cursor = conn.cursor()
		command = f"VACUUM FULL {table_name}";
		conn.commit()
		cursor.close()
		conn.close()
	
	def get_num_rows(self,table_name):
		conn = self.conn()
		cursor = conn.cursor()
		cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
		count = cursor.fetchone()[0]
		cursor.close()
		conn.close()
		return count
		
	def tracked_table_size(self,table_name):
		if(table_name not in self.index_counters):
			self.index_counters[table_name]={"deletions":0,"additions":0,"size":0}
			self.index_counters[table_name]["size"] = self.get_num_rows(table_name)
		return self.index_counters[table_name]["size"]
	
	def get_first_id(self,table_name):
		conn = self.conn()
		cursor = conn.cursor()
		command = f"SELECT MIN(Id) FROM {table_name} LIMIT 1;";
		cursor.execute(command)
		# id will be none if id is last id in the table
		first_id = cursor.fetchone()[0]
		cursor.close()
		conn.close()
		return first_id
	
	def get_next_id(self,table_name,id):
		conn = self.conn()
		cursor = conn.cursor()
		command = f"SELECT Id FROM {table_name} WHERE Id > {id} ORDER BY Id ASC LIMIT 1;";
		cursor.execute(command)
		# id will be none if id is last id in the table
		next_id = cursor.fetchone()
		if(next_id!=None):
			next_id = next_id[0]
		cursor.close()
		conn.close()
		return next_id
		
	def get_all_id(self,table_name):
		conn = self.conn()
		cursor = conn.cursor()
		command = f"SELECT Id FROM {table_name} ORDER BY Id ASC";
		cursor.execute(command)
		ids = cursor.fetchall()
		# return only the ids of each row returned
		return [x[0] for x in ids]
		
	def similarity_search(self,table_name,query,top_k=5,max_k=10,columns=["embedding_text"]):
		conn = self.conn()
		cursor = conn.cursor()
		results = []
		query_embedding = self.embedders.get_embeddings(query)
		for key,value in query_embedding.items():
			#
			# strange case here. For some reason we need to type cast to vector when using the pgdistance function
			#
			command="SELECT Id,"+", ".join(columns)+f", {key}_embedding <-> %s::vector AS distance FROM {table_name} ORDER BY distance LIMIT %s"
			cursor.execute(command,(value.tolist(),top_k))
			results.append(cursor.fetchall())
		cursor.close()
		conn.close()
		unique_sets = []
		for i in range(len(results[0])):
			for j in range(len(results)):
				unique_sets.append(tuple(results[j][i][:-1]))
		return list(dict.fromkeys(unique_sets))[:max_k]