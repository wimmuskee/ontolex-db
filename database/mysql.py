# -*- coding: utf-8 -*-

import pymysql.cursors
import uuid

"""
Some explanation for this set of functions.

set: put a partical subset in a class var
insert: insert one row without checks and dependencies, optionally commit
store: insert multiples and calling separate insert functions, always commits and has optional safemode

todo, add, find and get
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
		query = "SELECT form.lexicalEntryID, form.lexicalFormID, type, rep.value AS rep_value, lex.identifier AS lex_identifier, form.identifier AS form_identifier FROM lexicalForm AS form \
			LEFT JOIN lexicalEntry AS lex ON form.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN writtenRep AS rep ON form.lexicalFormID = rep.lexicalFormID \
			WHERE rep.languageID = %s"
		c.execute(query, (lang_id))
		self.lexicalForms = c.fetchall()
		c.close()


	def setLexicalForm(self,lexicalEntryID,lang_id):
		c = self.DB.cursor()
		query = "SELECT form.lexicalEntryID, form.lexicalFormID, type, rep.value AS rep_value, lex.identifier AS lex_identifier, form.identifier AS form_identifier FROM lexicalForm AS form \
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
		self.lexicalSenses = []
		c = self.DB.cursor()
		query = "SELECT sense.lexicalSenseID, sense.lexicalEntryID, lex.identifier AS lex_identifier, sense.identifier AS sense_identifier FROM lexicalSense AS sense \
			LEFT JOIN lexicalEntry AS lex ON sense.lexicalEntryID = lex.lexicalEntryID \
			WHERE sense.lexicalEntryID = %s"
		c.execute(query, (lexicalEntryID))
		self.lexicalSenses = c.fetchall()
		c.close()


	def setLexicalSensesByEntries(self):
		c = self.DB.cursor()
		for entry in self.lexicalEntries:
			query = "SELECT sense.lexicalSenseID, sense.lexicalEntryID, lex.identifier AS lex_identifier, sense.identifier AS sense_identifier FROM lexicalSense AS sense \
				LEFT JOIN lexicalEntry AS lex ON sense.lexicalEntryID = lex.lexicalEntryID \
				WHERE sense.lexicalEntryID = %s"
			c.execute(query, (entry["lexicalEntryID"]))
			self.lexicalSenses.extend(c.fetchall())
		c.close()


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


	def getLexicalEntryID(self,value,partOfSpeechID):
		c = self.DB.cursor()
		query = "SELECT lexicalEntryID FROM lexicalEntry WHERE value = %s AND partOfSpeechID = %s"
		c.execute(query, (value,partOfSpeechID))
		row = c.fetchone()
		c.close()
		return row["lexicalEntryID"]


	def getID(self,identifier,table):
		""" Return the real database ID from either entry, form or sense, based on identifier. """
		c = self.DB.cursor()
		field = table + "ID"
		query = "SELECT " + field + " FROM " + table + " WHERE identifier = %s"
		c.execute(query,(identifier))
		row = c.fetchone()
		c.close()
		return row[field]


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


	def addSense(self,source_value,source_pos_id,namespace,property,target_value,target_pos_id):
		# property and namespace are not validated right now
		sourceLexicalEntryID = self.getLexicalEntryID(source_value,source_pos_id)
		sourceLexicalSenseID = self.storeLexicalSense(sourceLexicalEntryID)

		if target_pos_id:
			targetLexicalEntryID = self.getLexicalEntryID(target_value,target_pos_id)
			targetLexicalSenseID = self.storeLexicalSense(targetLexicalEntryID)
			reference = self.__getLexicalSenseIdentifier(targetLexicalSenseID)
		else:
			reference = target_value
		
		self.storeSenseReference(sourceLexicalSenseID,namespace,property,reference)
		self.DB.commit()


	def storeLexicalSense(self,lexicalEntryID):
		""" This safely stores max 1 lexicalSense for the lexicalEntryID. """
		self.setLexicalSensesByID(lexicalEntryID)
		sensecount = len(self.lexicalSenses) 
		if sensecount > 1:
			print("error, more senses")
			exit()
		elif sensecount == 1:
			lexicalSenseID = self.lexicalSenses[0]["lexicalSenseID"]
		elif sensecount == 0:
			lexicalSenseID = self.insertLexicalSense(lexicalEntryID)

		self.DB.commit()
		return lexicalSenseID


	def storeSenseReference(self,lexicalSenseID,namespace,property,reference):
		c = self.DB.cursor()
		query = "INSERT INTO senseReference (lexicalSenseID,namespace,property,reference) VALUES (%s,%s,%s,%s)"
		c.execute(query, (lexicalSenseID,namespace,property,reference))
		c.close()


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


	def __getLexicalSenseIdentifier(self,lexicalSenseID):
		c = self.DB.cursor()
		query = "SELECT identifier FROM lexicalSense WHERE lexicalSenseID = %s"
		c.execute(query, (lexicalSenseID))
		row = c.fetchone()
		c.close()
		return row["identifier"]
