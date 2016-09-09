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


	def connect(self):
		self.DB = pymysql.connect(host=self.host,user=self.user, passwd=self.passwd,db=self.name,charset='utf8',use_unicode=1,cursorclass=pymysql.cursors.DictCursor)


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

