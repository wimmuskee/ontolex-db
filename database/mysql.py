# -*- coding: utf-8 -*-

import pymysql.cursors


class Database:
	def __init__(self,config):
		self.host = config["host"]
		self.user = config["user"]
		self.passwd = config["passwd"]
		self.name = config["name"]
		self.lexicalEntries = []
		self.lexicalEntryIDs = []
		self.lexicalForms = []
		self.posses = {}
		self.languages = {}


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


	def setLexicalEntries(self):
		c = self.DB.cursor()
		query = "SELECT lexicalEntryID, class, lex.value AS lex_value, pos.value AS pos_value FROM lexicalEntry AS lex \
			LEFT JOIN partOfSpeechVocabulary AS pos ON lex.partOfSpeechID = pos.id"
		c.execute(query)
		self.lexicalEntries = c.fetchall()
		c.close()
		for entry in self.lexicalEntries:
			self.lexicalEntryIDs.append(entry["lexicalEntryID"])


	def setLexicalForms(self,lang):
		c = self.DB.cursor()
		query = "SELECT form.lexicalEntryID, form.lexicalFormID, type, rep.value AS rep_value, lex.value AS lex_value, lang.iso_639_1 FROM lexicalForm AS form \
			LEFT JOIN lexicalEntry AS lex ON form.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN writtenRep AS rep ON form.lexicalFormID = rep.lexicalFormID \
			LEFT JOIN languageVocabulary AS lang ON rep.languageID = lang.id \
			WHERE iso_639_1 = %s"
		c.execute(query, (lang))
		self.lexicalForms = c.fetchall()
		c.close()


	def setLexicalEntry(self,identifier):
		c = self.DB.cursor()
		query = "SELECT lexicalEntryID, class, lex.value AS lex_value, pos.value AS pos_value FROM lexicalEntry AS lex \
			LEFT JOIN partOfSpeechVocabulary AS pos ON lex.partOfSpeechID = pos.id \
			WHERE lexicalEntryID = %s"
		c.execute(query, (identifier))
		self.lexicalEntries = c.fetchall()
		c.close()


	def setLexicalForm(self,identifier,lang):
		c = self.DB.cursor()
		query = "SELECT form.lexicalEntryID, form.lexicalFormID, type, rep.value AS rep_value, lex.value AS lex_value, lang.iso_639_1 FROM lexicalForm AS form \
			LEFT JOIN lexicalEntry AS lex ON form.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN writtenRep AS rep ON form.lexicalFormID = rep.lexicalFormID \
			LEFT JOIN languageVocabulary AS lang ON rep.languageID = lang.id \
			WHERE form.lexicalEntryID = %s \
			AND iso_639_1 = %s"
		c.execute(query, (identifier,lang))
		self.lexicalForms = c.fetchall()
		c.close()


	def storeCanonical(self,word,lang_id,pos_id):
		lexicalEntryID = self.__storeLexicalEntry(word,pos_id)
		lexicalFormID = self.storeForm(lexicalEntryID,"canonicalForm")
		self.storeWrittenRep(lexicalFormID,word,lang_id)
		self.DB.commit()


	def storeForm(self,lexicalEntryID,type):
		c = self.DB.cursor()
		query = "INSERT INTO lexicalForm (lexicalEntryID,type) VALUES (%s,%s)"
		c.execute(query, (lexicalEntryID,type))
		lexicalFormID = c.lastrowid
		c.close()
		return lexicalFormID


	def storeWrittenRep(self,lexicalFormID,word,lang_id):
		c = self.DB.cursor()
		query = "INSERT INTO writtenRep (lexicalFormID,languageID,value) VALUES (%s,%s,%s)"
		c.execute(query, (lexicalFormID,lang_id,word))
		c.close()
		

	def __storeLexicalEntry(self,word,pos_id):
		c = self.DB.cursor()
		query = "INSERT INTO lexicalEntry (value,partOfSpeechID) VALUES (%s,%s)"
		c.execute(query, (word,pos_id))
		lexicalEntryID = c.lastrowid
		c.close()
		return lexicalEntryID