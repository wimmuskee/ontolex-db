# -*- coding: utf-8 -*-

import pymysql.cursors
import uuid

class Database:
	def __init__(self,config):
		self.host = config["host"]
		self.user = config["user"]
		self.passwd = config["passwd"]
		self.name = config["name"]
		self.lexicalEntries = []
		self.lexicalEntryIDs = []
		self.lexicalForms = []
		self.lexicalProperties = []
		self.lexicalSenses = []
		self.senseReferences = []
		self.posses = {}
		self.languages = {}
		self.morphosyntactics = {}


	def connect(self):
		self.DB = pymysql.connect(host=self.host,user=self.user, passwd=self.passwd,db=self.name,charset='utf8',use_unicode=1,cursorclass=pymysql.cursors.DictCursor)


	def setPosses(self):
		c = self.DB.cursor()
		query = "SELECT * FROM partOfSpeechVocabulary"
		c.execute(query)
		for row in c.fetchall():
			self.posses[row["value"]] = row["id"]


	def setLanguages(self):
		c = self.DB.cursor()
		query = "SELECT * FROM languageVocabulary"
		c.execute(query)
		for row in c.fetchall():
			self.languages[row["iso_639_1"]] = row["id"]


	def setMorphoSyntactics(self):
		c = self.DB.cursor()
		query = "SELECT * FROM morphoSyntacticsVocabulary"
		c.execute(query)
		for row in c.fetchall():
			key = row["property"] + ":" + row["value"]
			self.morphosyntactics[key] = row["id"]


	def setLexicalEntries(self):
		c = self.DB.cursor()
		query = "SELECT lexicalEntryID, class, lex.value AS lex_value, pos.value AS pos_value, lex.identifier AS lex_identifier FROM lexicalEntry AS lex \
			LEFT JOIN partOfSpeechVocabulary AS pos ON lex.partOfSpeechID = pos.id"
		c.execute(query)
		self.lexicalEntries = c.fetchall()
		c.close()
		for entry in self.lexicalEntries:
			self.lexicalEntryIDs.append(entry["lexicalEntryID"])


	def setLexicalForms(self,lang):
		c = self.DB.cursor()
		query = "SELECT form.lexicalEntryID, form.lexicalFormID, type, rep.value AS rep_value, lex.value AS lex_value, lex.identifier AS lex_identifier, form.identifier AS form_identifier, lang.iso_639_1 FROM lexicalForm AS form \
			LEFT JOIN lexicalEntry AS lex ON form.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN writtenRep AS rep ON form.lexicalFormID = rep.lexicalFormID \
			LEFT JOIN languageVocabulary AS lang ON rep.languageID = lang.id \
			WHERE iso_639_1 = %s"
		c.execute(query, (lang))
		self.lexicalForms = c.fetchall()
		c.close()


	def setLexicalEntry(self,lexicalEntryID):
		c = self.DB.cursor()
		query = "SELECT lexicalEntryID, class, lex.value AS lex_value, pos.value AS pos_value, identifier AS lex_identifier FROM lexicalEntry AS lex \
			LEFT JOIN partOfSpeechVocabulary AS pos ON lex.partOfSpeechID = pos.id \
			WHERE lexicalEntryID = %s"
		c.execute(query, (lexicalEntryID))
		self.lexicalEntries = c.fetchall()
		c.close()


	def setLexicalForm(self,lexicalEntryID,lang):
		c = self.DB.cursor()
		query = "SELECT form.lexicalEntryID, form.lexicalFormID, type, rep.value AS rep_value, lex.identifier AS lex_identifier, lex.value AS lex_value, form.identifier AS form_identifier, lang.iso_639_1 FROM lexicalForm AS form \
			LEFT JOIN lexicalEntry AS lex ON form.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN writtenRep AS rep ON form.lexicalFormID = rep.lexicalFormID \
			LEFT JOIN languageVocabulary AS lang ON rep.languageID = lang.id \
			WHERE form.lexicalEntryID = %s \
			AND iso_639_1 = %s"
		c.execute(query, (lexicalEntryID,lang))
		self.lexicalForms = c.fetchall()
		c.close()


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
		query = "SELECT lex.value AS lex_value, lexicalSenseID, sense.lexicalEntryID, lex.identifier AS lex_identifier, sense.identifier AS sense_identifier FROM lexicalSense AS sense \
			LEFT JOIN lexicalEntry AS lex ON sense.lexicalEntryID = lex.lexicalEntryID"
		c.execute(query)
		self.lexicalSenses = c.fetchall()
		c.close()


	def setLexicalSensesByID(self,lexicalEntryID):
		c = self.DB.cursor()
		query = "SELECT lex.value AS lex_value, lexicalSenseID, sense.lexicalEntryID, lex.identifier AS lex_identifier, sense.identifier AS sense_identifier FROM lexicalSense AS sense \
			LEFT JOIN lexicalEntry AS lex ON sense.lexicalEntryID = lex.lexicalEntryID \
			WHERE sense.lexicalEntryID = %s"
		c.execute(query, (lexicalEntryID))
		self.lexicalSenses = c.fetchall()
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


	def storeCanonical(self,word,lang_id,pos_id):
		""" Stores new lexicalEntry and canonicalForm if entry does not exist."""
		if self.findLexicalEntry(word,pos_id):
			return None
		
		lexicalEntryID = self.__storeLexicalEntry(word,pos_id)
		lexicalFormID = self.storeForm(lexicalEntryID,"canonicalForm")
		self.storeWrittenRep(lexicalFormID,word,lang_id)
		self.DB.commit()
		return lexicalEntryID


	def storeOtherForm(self,lexicalEntryID,word,lang_id,properties):
		lexicalFormID = self.storeForm(lexicalEntryID,"otherForm")
		self.storeWrittenRep(lexicalFormID,word,lang_id)
		for property in properties:
			# p in form <property>:<value>
			self.storeFormProperty(lexicalFormID,self.morphosyntactics[property])
		self.DB.commit()


	def storeForm(self,lexicalEntryID,type):
		c = self.DB.cursor()
		identifier = "urn:uuid:" + str(uuid.uuid4())
		query = "INSERT INTO lexicalForm (lexicalEntryID,identifier,type) VALUES (%s,%s,%s)"
		c.execute(query, (lexicalEntryID,identifier,type))
		lexicalFormID = c.lastrowid
		c.close()
		return lexicalFormID


	def storeWrittenRep(self,lexicalFormID,word,lang_id):
		c = self.DB.cursor()
		query = "INSERT INTO writtenRep (lexicalFormID,languageID,value) VALUES (%s,%s,%s)"
		c.execute(query, (lexicalFormID,lang_id,word))
		c.close()


	def storeFormProperty(self,lexicalFormID,morphoSyntacticsID):
		c = self.DB.cursor()
		query = "INSERT INTO formMorphoSyntactics (lexicalFormID,morphoSyntacticsID) VALUES (%s,%s)"
		c.execute(query, (lexicalFormID,morphoSyntacticsID))
		c.close()


	def findLexicalEntry(self,word,pos_id):
		c = self.DB.cursor()
		query = "SELECT lexicalEntryID FROM lexicalEntry WHERE value = %s AND partOfSpeechID = %s"
		c.execute(query, (word,pos_id))
		row = c.fetchone()
		
		if row:
			return row["lexicalEntryID"]
		else:
			return None


	def __storeLexicalEntry(self,word,pos_id):
		c = self.DB.cursor()
		identifier = "urn:uuid:" + str(uuid.uuid4())
		query = "INSERT INTO lexicalEntry (value,identifier,partOfSpeechID) VALUES (%s,%s,%s)"
		c.execute(query, (word,identifier,pos_id))
		lexicalEntryID = c.lastrowid
		c.close()
		return lexicalEntryID