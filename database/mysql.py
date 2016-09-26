# -*- coding: utf-8 -*-

import pymysql.cursors
import uuid

"""
Some explanation for this set of functions.

set: put a partical subset in a class var
insert: insert one row without checks and dependencies, optionally commit
store: insert multiples and calling separate insert functions, always commits and has optional safemode
check: returns True or False
get: get an individual value

todo, find and get
"""

class Database:
	def __init__(self,config):
		self.host = config["host"]
		self.user = config["user"]
		self.passwd = config["passwd"]
		self.name = config["name"]
		self.lexicalEntries = []
		self.lexicalForms = []
		self.lexicalProperties = []
		self.lexicalSenses = []
		self.senseReferences = []
		self.lexicalEntryComponents = []
		self.components = []
		self.lexicalEntryLabels = {}
		self.lexicalSenseDefinitions = {}
		self.posses = {}
		self.languages = {}
		self.morphosyntactics = {}
		self.senserelations = []


	def connect(self):
		self.DB = pymysql.connect(host=self.host,user=self.user, passwd=self.passwd,db=self.name,charset='utf8',use_unicode=1,cursorclass=pymysql.cursors.DictCursor)


	def setPosses(self):
		c = self.DB.cursor()
		query = "SELECT * FROM partOfSpeechVocabulary"
		c.execute(query)
		for row in c.fetchall():
			self.posses[row["value"]] = row["id"]
		c.close()


	def setLanguages(self):
		c = self.DB.cursor()
		query = "SELECT * FROM languageVocabulary"
		c.execute(query)
		for row in c.fetchall():
			self.languages[row["iso_639_1"]] = row["id"]
		c.close()


	def setMorphoSyntactics(self):
		c = self.DB.cursor()
		query = "SELECT * FROM morphoSyntacticsVocabulary"
		c.execute(query)
		for row in c.fetchall():
			key = row["property"] + ":" + row["value"]
			self.morphosyntactics[key] = row["id"]
		c.close()


	def setSenseRelations(self):
		""" Should not be manual, but for now there is validation. """
		self.senserelations.extend( ["ontolex:reference"] )
		self.senserelations.extend( ["skos:broader", "skos:related", "skos:exactMatch"] )
		self.senserelations.extend( ["skos-thes:broaderInstantial", "skos-thes:broaderPartitive"] )
		self.senserelations.extend( ["lexinfo:antonym"] )


	def setLexicalEntries(self):
		c = self.DB.cursor()
		query = "SELECT lexicalEntryID, class, pos.value AS pos_value, lex.identifier AS lex_identifier FROM lexicalEntry AS lex \
			LEFT JOIN partOfSpeechVocabulary AS pos ON lex.partOfSpeechID = pos.id"
		c.execute(query)
		self.lexicalEntries = c.fetchall()
		c.close()


	def setLexicalEntriesByPOS(self,pos_id):
		c = self.DB.cursor()
		query = "SELECT lexicalEntryID, class, pos.value AS pos_value, lex.identifier AS lex_identifier FROM lexicalEntry AS lex \
			LEFT JOIN partOfSpeechVocabulary AS pos ON lex.partOfSpeechID = pos.id \
			WHERE lex.partOfSpeechID = %s"
		c.execute(query, (pos_id))
		self.lexicalEntries = c.fetchall()
		c.close()


	def setLexicalEntry(self,lexicalEntryID):
		c = self.DB.cursor()
		query = "SELECT lexicalEntryID, class, pos.value AS pos_value, identifier AS lex_identifier FROM lexicalEntry AS lex \
			LEFT JOIN partOfSpeechVocabulary AS pos ON lex.partOfSpeechID = pos.id \
			WHERE lexicalEntryID = %s"
		c.execute(query, (lexicalEntryID))
		self.lexicalEntries = c.fetchall()
		c.close()


	def setLexicalForms(self,lang_id):
		c = self.DB.cursor()
		query = "SELECT form.lexicalEntryID, form.lexicalFormID, type, rep.value AS rep_value, lex.identifier AS lex_identifier, form.identifier AS form_identifier, rep.syllableCount AS syllableCount FROM lexicalForm AS form \
			LEFT JOIN lexicalEntry AS lex ON form.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN writtenRep AS rep ON form.lexicalFormID = rep.lexicalFormID \
			WHERE rep.languageID = %s"
		c.execute(query, (lang_id))
		self.lexicalForms = c.fetchall()
		c.close()


	def setLexicalForm(self,lexicalEntryID,lang_id):
		c = self.DB.cursor()
		query = "SELECT form.lexicalEntryID, form.lexicalFormID, type, rep.value AS rep_value, lex.identifier AS lex_identifier, form.identifier AS form_identifier, rep.syllableCount AS syllableCount FROM lexicalForm AS form \
			LEFT JOIN lexicalEntry AS lex ON form.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN writtenRep AS rep ON form.lexicalFormID = rep.lexicalFormID \
			WHERE form.lexicalEntryID = %s \
			AND rep.languageID = %s"
		c.execute(query, (lexicalEntryID,lang_id))
		self.lexicalForms.extend(c.fetchall())
		c.close()


	def setLexicalFormsByEntries(self,lang_id):
		for entry in self.lexicalEntries:
			self.setLexicalForm(entry["lexicalEntryID"],lang_id)


	def setLexicalEntryLabels(self):
		""" Sets easy lookup labels for use in setLexicalSenses without needing big joins.
		Called seperately because setLexicalFormsByEntries calls setLexicalForm. """
		for form in self.lexicalForms:
			if form["type"] == "canonicalForm":
				self.lexicalEntryLabels[form["lexicalEntryID"]] = form["rep_value"]


	def setLexicalFormProperties(self):
		c = self.DB.cursor()
		for form in self.lexicalForms:
			propertydict = { "form_identifier": form["form_identifier"], "properties": [] }
			query = "SELECT vocab.property, vocab.value FROM formMorphoSyntactics AS formprop \
				LEFT JOIN morphoSyntacticsVocabulary AS vocab ON formprop.morphoSyntacticsID = vocab.id \
				WHERE formprop.lexicalFormID = %s"
			c.execute(query, (form["lexicalFormID"]))
			if c.rowcount > 0:
				propertydict["properties"] = c.fetchall()
			
			self.lexicalProperties.append(propertydict)
		c.close()


	def setLexicalSenses(self):
		c = self.DB.cursor()
		query = "SELECT sense.lexicalSenseID, sense.lexicalEntryID, lex.identifier AS lex_identifier, sense.identifier AS sense_identifier FROM lexicalSense AS sense \
			LEFT JOIN lexicalEntry AS lex ON sense.lexicalEntryID = lex.lexicalEntryID"
		c.execute(query)
		self.lexicalSenses = c.fetchall()
		c.close()


	def setLexicalSensesByID(self,lexicalEntryID):
		c = self.DB.cursor()
		query = "SELECT sense.lexicalSenseID, sense.lexicalEntryID, lex.identifier AS lex_identifier, sense.identifier AS sense_identifier FROM lexicalSense AS sense \
			LEFT JOIN lexicalEntry AS lex ON sense.lexicalEntryID = lex.lexicalEntryID \
			WHERE sense.lexicalEntryID = %s"
		c.execute(query, (lexicalEntryID))
		self.lexicalSenses.extend(c.fetchall())
		c.close()


	def setLexicalSensesByEntries(self):
		for entry in self.lexicalEntries:
			self.setLexicalSensesByID(entry["lexicalEntryID"])


	def setSenseDefinitions(self,lang_id):
		""" Definition is optional."""
		c = self.DB.cursor()
		for sense in self.lexicalSenses:
			query = "SELECT value FROM senseDefinition WHERE lexicalSenseID = %s AND languageID = %s"
			c.execute(query, (sense["lexicalSenseID"],lang_id))
			row = c.fetchone()
			
			if row:
				self.lexicalSenseDefinitions[sense["sense_identifier"]] = row["value"]
		c.close()


	def setSenseReferences(self):
		c = self.DB.cursor()
		for sense in self.lexicalSenses:
			propertydict = { "sense_identifier": sense["sense_identifier"], "references": [] }
			query = "SELECT namespace, property, reference FROM senseReference \
				WHERE lexicalSenseID = %s"
			c.execute(query, (sense["lexicalSenseID"]))
			if c.rowcount > 0:
				propertydict["references"] = c.fetchall()

			self.senseReferences.append( propertydict )
		c.close()


	def setLexicalComponents(self):
		c = self.DB.cursor()
		query = "SELECT lex.identifier AS lex_identifier, comp.identifier AS comp_identifier, position FROM lexicalEntryComponent AS lexcomp \
			LEFT JOIN lexicalEntry AS lex ON lexcomp.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN component AS comp ON lexcomp.componentID = comp.componentID"
		c.execute(query)
		self.lexicalEntryComponents.extend(c.fetchall())
		c.close()


	def setLexicalComponentsByID(self,lexicalEntryID):
		c = self.DB.cursor()
		query = "SELECT lex.identifier AS lex_identifier, comp.identifier AS comp_identifier, position FROM lexicalEntryComponent AS lexcomp \
			LEFT JOIN lexicalEntry AS lex ON lexcomp.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN component AS comp ON lexcomp.componentID = comp.componentID \
			WHERE lexcomp.lexicalEntryID = %s"
		c.execute(query, (lexicalEntryID))
		self.lexicalEntryComponents.extend(c.fetchall())
		c.close()


	def setComponents(self):
		c = self.DB.cursor()
		query = "SELECT DISTINCT comp.identifier AS comp_identifier, lex.identifier AS lex_identifier, form.identifier AS form_identifier FROM component AS comp \
			LEFT JOIN lexicalEntry AS lex ON comp.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN lexicalForm AS form ON comp.lexicalFormID = form.lexicalFormID"
		c.execute(query)
		self.components.extend(c.fetchall())
		c.close()


	def setComponentsByID(self,lexicalEntryID,lang_id):
		c = self.DB.cursor()
		query = "SELECT DISTINCT comp.identifier AS comp_identifier, lex.identifier AS lex_identifier, form.identifier AS form_identifier, rep.value AS rep_value FROM component AS comp \
			LEFT JOIN lexicalEntryComponent AS lexcomp ON comp.componentID = lexcomp.componentID \
			LEFT JOIN lexicalEntry AS lex ON comp.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN lexicalForm AS form ON comp.lexicalFormID = form.lexicalFormID \
			LEFT JOIN writtenRep AS rep ON form.lexicalFormID = rep.lexicalFormID \
			WHERE lexcomp.lexicalEntryID = %s \
			AND rep.languageID = %s"
		c.execute(query, (lexicalEntryID,lang_id))
		self.components.extend(c.fetchall())
		c.close()


	def getLexicalEntryID(self,value,partOfSpeechID):
		c = self.DB.cursor()
		query = "SELECT lexicalEntryID FROM lexicalEntry WHERE value = %s AND partOfSpeechID = %s"
		c.execute(query, (value,partOfSpeechID))
		row = c.fetchone()
		c.close()
		return row["lexicalEntryID"]


	def getLexicalSenseID(self,lexicalEntryID):
		c = self.DB.cursor()
		query = "SELECT lexicalSenseID FROM lexicalSense WHERE lexicalEntryID = %s"
		c.execute(query,(lexicalEntryID))
		row = c.fetchone()
		c.close()
		return row["lexicalSenseID"]


	def getID(self,identifier,table):
		""" Return the real database ID from either entry, form or sense, based on identifier. """
		c = self.DB.cursor()
		field = table + "ID"
		query = "SELECT " + field + " FROM " + table + " WHERE identifier = %s"
		c.execute(query,(identifier))
		row = c.fetchone()
		c.close()
		return row[field]


	def getCountlexicalSenses(self,lexicalEntryID):
		c = self.DB.cursor()
		query = "SELECT count(*) AS count FROM lexicalSense WHERE lexicalEntryID = %s"
		c.execute(query,(lexicalEntryID))
		row = c.fetchone()
		c.close()
		return int(row["count"])


	def checkSenseReferenceExists(self,lexicalSenseID,relation,reference):
		c = self.DB.cursor()
		namespace = relation.split(":")[0]
		property = relation.split(":")[1]
		query = "SELECT * FROM senseReference WHERE lexicalSenseID = %s AND namespace = %s AND property = %s AND reference = %s"
		c.execute(query,(lexicalSenseID,namespace,property,reference))
		row = c.fetchone()
		if row:
			return True
		else:
			return False


	def storeCanonical(self,word,lang_id,pos_id,safemode=True):
		""" Stores new lexicalEntry and canonicalForm if entry does not exist."""
		if self.findLexicalEntry(word,pos_id) and safemode:
			print("found this entry already: " + word)
			return None

		lexicalEntryID = self.insertLexicalEntry(word,pos_id)
		lexicalFormID = self.insertLexicalForm(lexicalEntryID,"canonicalForm")
		self.insertWrittenRep(lexicalFormID,word,lang_id)
		self.DB.commit()
		return lexicalEntryID


	def storeOtherForm(self,lexicalEntryID,word,lang_id,safemode=True):
		if self.findlexicalForm(lexicalEntryID,word,lang_id) and safemode:
			print("found this form already: " + word)
			return None

		lexicalFormID = self.insertLexicalForm(lexicalEntryID,"otherForm")
		self.insertWrittenRep(lexicalFormID,word,lang_id)
		self.DB.commit()
		return lexicalFormID


	def storeFormProperties(self,lexicalFormID,properties,safemode=True):
		# no safemode yet

		for property in properties:
			# p in form <property>:<value>
			self.insertFormProperty(lexicalFormID,self.morphosyntactics[property])
		self.DB.commit()


	def storeLexicalSense(self,lexicalEntryID,relation,reference,safemode=True):
		""" Adds lexicalSense to lexicxalEntry, and adds a relation. """
		senseCount = self.getCountlexicalSenses(lexicalEntryID)
		
		if senseCount == 0:
			# no senses yet, we can safely add a sense and a relation
			lexicalSenseID = self.insertLexicalSense(lexicalEntryID)
			self.insertSenseReference(lexicalSenseID,relation,reference)
		elif senseCount == 1:
			# asume we're adding to this sense, retrieve the senseID and add reference if not exists
			lexicalSenseID = self.getLexicalSenseID(lexicalEntryID)
			if not self.checkSenseReferenceExists(lexicalSenseID,relation,reference):
				self.insertSenseReference(lexicalSenseID,relation,reference)
		else:
			lexicalSenseID = None

		self.DB.commit()
		return lexicalSenseID


	def storeComponent(self,lexicalFormID):
		""" Stores component, based on lexicalFormID. """
		c = self.DB.cursor()
		query = "SELECT lexicalEntryID FROM lexicalForm WHERE lexicalFormID = %s"
		c.execute(query,(lexicalFormID))
		row = c.fetchone()
		
		if row:
			return self.insertComponent(row["lexicalEntryID"],lexicalFormID,True)
		else:
			return "failed"


	def findLexicalEntry(self,word,pos_id):
		c = self.DB.cursor()
		query = "SELECT lexicalEntryID FROM lexicalEntry WHERE value = %s AND partOfSpeechID = %s"
		c.execute(query, (word,pos_id))
		row = c.fetchone()
		c.close()

		if row:
			return row["lexicalEntryID"]
		else:
			return None


	def findlexicalForm(self,lexicalEntryID,word,lang_id):
		c = self.DB.cursor()
		query = "SELECT form.lexicalFormID FROM lexicalForm AS form \
			LEFT JOIN writtenRep AS rep ON form.lexicalFormID = rep.lexicalFormID \
			WHERE form.lexicalEntryID = %s \
			AND rep.value = %s \
			AND rep.languageID = %s"
		c.execute(query, (lexicalEntryID,word,lang_id))
		row = c.fetchone()
		c.close()

		if row:
			return row["lexicalFormID"]
		else:
			return None


	def insertLexicalEntry(self,word,pos_id,commit=False):
		c = self.DB.cursor()
		entryclass = "Word"
		if word.count(" ") > 0:
			entryclass = "MultiwordExpression"

		identifier = "urn:uuid:" + str(uuid.uuid4())
		query = "INSERT INTO lexicalEntry (value,identifier,partOfSpeechID,class) VALUES (%s,%s,%s,%s)"
		c.execute(query, (word,identifier,pos_id,entryclass))
		lexicalEntryID = c.lastrowid
		c.close()
		if commit:
			self.DB.commit()

		return lexicalEntryID


	def insertLexicalForm(self,lexicalEntryID,type,commit=False):
		c = self.DB.cursor()
		identifier = "urn:uuid:" + str(uuid.uuid4())
		query = "INSERT INTO lexicalForm (lexicalEntryID,identifier,type) VALUES (%s,%s,%s)"
		c.execute(query, (lexicalEntryID,identifier,type))
		lexicalFormID = c.lastrowid
		c.close()
		if commit:
			self.DB.commit()

		return lexicalFormID


	def insertWrittenRep(self,lexicalFormID,word,lang_id,commit=False):
		c = self.DB.cursor()
		query = "INSERT INTO writtenRep (lexicalFormID,languageID,value) VALUES (%s,%s,%s)"
		c.execute(query, (lexicalFormID,lang_id,word))
		c.close()
		if commit:
			self.DB.commit()


	def insertFormProperty(self,lexicalFormID,morphoSyntacticsID,commit=False):
		c = self.DB.cursor()
		query = "INSERT INTO formMorphoSyntactics (lexicalFormID,morphoSyntacticsID) VALUES (%s,%s)"
		c.execute(query, (lexicalFormID,morphoSyntacticsID))
		c.close()
		if commit:
			self.DB.commit()


	def insertLexicalSense(self,lexicalEntryID,commit=False):
		""" Insert lexicalSense, and optionally commit."""
		c = self.DB.cursor()
		identifier = "urn:uuid:" + str(uuid.uuid4())
		query = "INSERT INTO lexicalSense (lexicalEntryID,identifier) VALUES (%s,%s)"
		c.execute(query, (lexicalEntryID,identifier))
		lexicalSenseID = c.lastrowid
		c.close()
		if commit:
			self.DB.commit()

		return lexicalSenseID


	def insertLexicalSenseDefinition(self,lexicalSenseID,languageID,definition,commit=False):
		c = self.DB.cursor()
		query = "INSERT INTO senseDefinition (lexicalSenseID,languageID,value) VALUES (%s,%s,%s)"
		c.execute(query, (lexicalSenseID,languageID,definition))
		c.close()
		if commit:
			self.DB.commit()


	def insertSenseReference(self,lexicalSenseID,relation,reference,commit=False):
		c = self.DB.cursor()
		namespace = relation.split(":")[0]
		property = relation.split(":")[1]
		query = "INSERT INTO senseReference (lexicalSenseID,namespace,property,reference) VALUES (%s,%s,%s,%s)"
		c.execute(query, (lexicalSenseID,namespace,property,reference))
		c.close()
		if commit:
			self.DB.commit()


	def insertComponent(self,lexicalEntryID,lexicalFormID,commit=False):
		c = self.DB.cursor()
		
		# we should have a checkExists for this
		query = "SELECT componentID FROM component WHERE lexicalEntryID = %s AND lexicalFormID = %s"
		c.execute(query,(lexicalEntryID,lexicalFormID))
		row = c.fetchone()
		
		if row:
			return row["componentID"]
		else:
			identifier = "urn:uuid:" + str(uuid.uuid4())
			query = "INSERT INTO component (identifier,lexicalEntryID,lexicalFormID) VALUES (%s,%s,%s)"
			c.execute(query,(identifier,lexicalEntryID,lexicalFormID))
			componentID = c.lastrowid
			c.close()
			if commit:
				self.DB.commit()
			return componentID


	def insertLexicalEntryComponent(self,lexicalEntryID,componentID,position,commit=False):
		c = self.DB.cursor()
		
		# more another checkExists, where nothing is returned
		query = "SELECT * FROM lexicalEntryComponent WHERE lexicalEntryID = %s AND componentID = %s AND position = %s"
		c.execute(query,(lexicalEntryID,componentID,position))
		row = c.fetchone()
		
		if not row:
			query = "INSERT INTO lexicalEntryComponent (lexicalEntryID,componentID,position) VALUES (%s,%s,%s)"
			c.execute(query,(lexicalEntryID,componentID,position))
			c.close()
			if commit:
				self.DB.commit()


	def updateSyllableCount(self,lexicalFormID,syllableCount,languageID):
		c = self.DB.cursor()
		query = "UPDATE writtenRep SET syllableCount = %s WHERE lexicalFormID = %s AND languageID = %s"
		c.execute(query,(syllableCount,lexicalFormID,languageID))
		c.close()
		self.DB.commit()
