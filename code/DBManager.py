import sqlite3
import os

class QueryDB():
	def __init__(self,path):
		self.path = path
		os.makedirs(os.path.dirname(self.path), exist_ok=True)
		self.setup()
		
	def 	setup(self):
		pass
		
	def get_text(self,table_name,id):
		return ""
		
	def add_answer(self,table,text):
		return -1
		
class BookDB(QueryDB):
	
	def setup(self):
		conn = sqlite3.connect(self.path)
		cursor = conn.cursor()
		# Book summaries, text and notes. This is stored in a database that
		# is set up to make querying and setting up reference texts accessible to the LLMs
		# This table contains the summary texts and final text that will be used to generate the final book.
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS BookText (
			Id INTEGER PRIMARY KEY AUTOINCREMENT,
			Text TEXT NOT NULL,
			Extended TEXT NOT NULL,
			Vector BLOB NOT NULL,
			Start REAL,
			End REAL,
			Height INTEGER,
			Parent INTEGER,
			Next INTEGER,
			Previous INTEGER,
			FOREIGN KEY (Parent) REFERENCES BookText (Id),
			FOREIGN KEY (Next) REFERENCES BookText (Id),
			FOREIGN KEY (Previous) REFERENCES BookText (Id)
			);
		''')
		# Categories for notes and proper names
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS Category (
			Id INTEGER PRIMARY KEY AUTOINCREMENT,
			Name TEXT NOT NULL,
			Description TEXT NOT NULL
			);
		''')
		# Proper names used through the text. 
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS ProperName (
			Id INTEGER PRIMARY KEY AUTOINCREMENT,
			Name TEXT NOT NULL UNIQUE,
			CategoryId INTEGER,
			Description Text NOT NULL,
			Vector BLOB NOT NULL,
			Start REAL,
			End REAL,
			FOREIGN KEY (CategoryId) REFERENCES Category(Id)
			);
		''')
		# Notes on any topic that is related to the book text. Notes are often clarifications of other notes
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS Note (
			Id INTEGER PRIMARY KEY AUTOINCREMENT,
			Text TEXT NOT NULL,
			CategoryId INTEGER,
			Start REAL,
			End REAL,
			FOREIGN KEY (CategoryId) REFERENCES Category(Id)
			);
		''')
		# Proper names that are reference in specific summary texts or the final book text
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS BookPropername  (
			BookId INTEGER,
			PropernameId INTEGER,
			PRIMARY KEY (BookId, ProperNameId),
			FOREIGN KEY (BookId) REFERENCES BookText(Id),
			FOREIGN KEY (ProperNameId) REFERENCES ProperName(Id)
			);
		''')
		# Summary texts contain links to sub texts which go deeper into specifics of parts of the summary text
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS BookChild  (
			BookId INTEGER,
			ChildId INTEGER,
			PRIMARY KEY (BookId, ChildId),
			FOREIGN KEY (BookId) REFERENCES Book(Id),
			FOREIGN KEY (ChildId) REFERENCES Book(Id)
			);
		''')
		# Listing of proper names found in a specific note
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS NotePropername  (
			NoteId INTEGER,
			ProperNameId INTEGER,
			PRIMARY KEY (NoteId, ProperNameId),
			FOREIGN KEY (NoteId) REFERENCES Note(Id),
			FOREIGN KEY (ProperNameId) REFERENCES ProperName(Id)
			);
		''')
		# proper names which reference other proper names even in their most basic description
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS PropernamePropername  (
			ProperNameId INTEGER,
			ReferenceId INTEGER,
			Description TEXT NOT NULL,
			PRIMARY KEY (ProperNameId, ReferenceId),
			FOREIGN KEY (ProperNameId) REFERENCES Propername(Id),
			FOREIGN KEY (ReferenceId) REFERENCES Propername(Id)
			);
		''')
		# inital descriptor categories
		cursor.execute("INSERT OR IGNORE INTO Category (Name, Description) VALUES (?, ?);",("Event",'''
			Describes an event/occurrence.
		'''))
		cursor.execute("INSERT OR IGNORE INTO Category (Name, Description) VALUES (?, ?);",("Location",'''
			Describes an location/place.
		'''))
		cursor.execute("INSERT OR IGNORE INTO Category (Name, Description) VALUES (?, ?);",("Entity",'''
			Describes an person, organization, group, creature, being, etc
		'''))
		cursor.execute("INSERT OR IGNORE INTO Category (Name, Description) VALUES (?, ?);",("Convention",'''
			Describes a law or procedure that is agreed upon by any entities.
		'''))
		cursor.execute("INSERT OR IGNORE INTO Category (Name, Description) VALUES (?, ?);",("Natural Laws",'''
			The fundamental laws that describe how the universe works.
		'''))
		cursor.execute("INSERT OR IGNORE INTO Category (Name, Description) VALUES (?, ?);",("Algorithm",'''
			Describes or provides an algorithm that can be used to "calculate" some desired quantity. Some input should go in and have some result come out.
		'''))
		cursor.execute("INSERT OR IGNORE INTO Category (Name, Description) VALUES (?, ?);",("Relationship",'''
			Describes the relationship between two entities.
		'''))
		cursor.execute("INSERT OR IGNORE INTO Category (Name, Description) VALUES (?, ?);",("Temporal",'''
			Describes a temporal relationship between two entities, events etc.
		'''))
		cursor.execute("INSERT OR IGNORE INTO Category (Name, Description) VALUES (?, ?);",("Style",'''
			Item pertains to stylistic representations and descriptions of text.
		'''))
		conn.commit()
		conn.close()
		
	def get_text(self,table_name,id):
		conn = sqlite3.connect(self.path)
		cursor = conn.cursor()
		cursor.execute(f"SELECT Text FROM {table_name} WHERE Id = ?", (id,))
		text = cursor.fetchone()[0]
		conn.close()
		return text
		
	def add_answer(self,table_name,text):
		conn = sqlite3.connect(self.path)
		cursor = conn.cursor()
		id = -1
		if(table_name=="Note"):
			cursor.execute(f"INSERT OR IGNORE INTO {table_name} (Text) VALUES (?) RETURNING Id;",(text,))
			id = cursor.fetchone()[0]
		conn.commit()
		conn.close()
		return id
	
	def replace(self,table_name,text,id):
		conn = sqlite3.connect(self.path)
		cursor = conn.cursor()
		if(table_name=="Note"):
			cursor.execute(f"UPDATE {table_name} SET (Text) = ? WHERE id = ?;",(text,id))
		conn.commit()
		conn.close()