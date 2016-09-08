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


	def connect(self):
		self.DB = pymysql.connect(host=self.host,user=self.user, passwd=self.passwd,db=self.name,charset='utf8',use_unicode=1,cursorclass=pymysql.cursors.DictCursor)


	def setLexicalEntries(self):
		c = self.DB.cursor()
		query = "SELECT lexicalEntryID, class, pos.value AS pos_value, CONCAT('urn:lex_', lex.value, '_', lexicalEntryID) AS identifier FROM lexicalEntry AS lex LEFT JOIN partOfSpeechVocabulary AS pos ON lex.partOfSpeechID = pos.id"
		c.execute(query)
		self.lexicalEntries = c.fetchall()
		c.close()
		for entry in self.lexicalEntries:
			self.lexicalEntryIDs.append(entry["lexicalEntryID"])


	def setForms(self):
		c = self.DB.cursor()
