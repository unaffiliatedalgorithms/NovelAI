class dl_dict:
	def __init__(self,list=[]):
		self.forward = {}
		self.backward = {}
		self.head = None
		self.tail = None
		self.len = 0
		for l in list:
			self.insert_tail(l)
	
	# insert key2 after key in dld
	def insert_after(self,key,key2):
		if key not in self.forward:
			try:
				raise KeyError(f"{key} not found in list")
			except KeyError as e:
				print(f"Caught an error: {e}")
		elif key2 in self.forward:
			if(key2==key):
				print("it seems like some after self insert shenigans were planned here")
			else:
				print("Key to be inserted is already in list. Key will be removed and reinserted")
				self.delete(key2)
				self.insert_after(key2)
		else:
			self.len+=1
			#No issues with None in forward direction
			temp = self.forward[key]
			self.forward[key] = key2
			self.forward[key2] = temp
			self.backward[key2] = self.backward[key]
			if(temp==None):
				self.backward[temp] = key2
			else:
				self.tail = key2
	
	def insert_before(self,key,key2):
		if key not in self.forward:
			try:
				raise KeyError(f"{key} not found in list")
			except KeyError as e:
				print(f"Caught an error: {e}")
		elif key2 in self.forward:
			if(key2==key):
				print("it seems like some before self insert shenigans were planned here")
			else:
				print("Key to be inserted is already in list. Key will be removed and reinserted")
				self.delete(key2)
				self.insert_after(key2)
		else:
			self.len+=1
			#No issues with None in backward direction
			temp = self.backward[key]
			self.backward[key] = key2
			self.backward[key2] = temp
			self.forward[key2] = self.forward[key]
			if(temp==None):
				self.forward[temp] = key2
			else:
				self.head = key2
			
	def delete(self,key):
		if key not in self.forward:
			try:
				raise KeyError(f"{key} not found in list")
			except KeyError as e:
				print(f"Caught an error: {e}")
		else:
			self.len-=1
			prev = self.backward[key]
			next = self.forward[key]
			if(prev!=None):
				self.forward[prev] = next
			else:
				self.head = next
			if(next!=None):
				self.backward[next] = prev
			else:
				self.tail = prev
			del self.forward[key]
			del self.backward[key]
	
	def insert_tail(self,key):
		if key in self.forward:
			print("Key to be inserted is already in list. Key will be removed and reinserted")
			self.delete(key)
			self.insert_tail(key)
		else:
			self.len+=1
			self.forward[key] = None
			if(self.tail!=None):
				self.backward[key] = self.tail
				self.forward[self.tail] = key
				self.tail = key
			# first element inserted
			else:
				self.backward[key] = None
				self.head = key
				self.tail = key
			
	def insert_head(self,key):
		if key in self.forward:
			print("Key to be inserted is already in list. Key will be removed and reinserted")
			self.delete(key)
			self.insert_head(key)
		else:
			self.len+=1
			self.backward[key] = None
			if(self.head!=None):
				self.forward[key] = self.head
				self.backward[self.head] = key
				self.head = key
			# first element inserted
			else:
				self.forward[key] = None
				self.tail = key
				self.head = key