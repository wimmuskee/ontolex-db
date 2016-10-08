# -*- coding: utf-8 -*-

import pymysql.cursors
import uuid
from urllib.parse import urlparse

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
		self.lexicalEntryRelations = []
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
		self.properties = {}
		self.senserelations = []
		self.entryrelations = {}


	def connect(self):
		self.DB = pymysql.connect(host=self.host,user=self.user, passwd=self.passwd,db=self.name,charset='utf8',use_unicode=1,cursorclass=pymysql.cursors.DictCursor)


	def setPosses(self):
		for row in self.__getRows("SELECT * FROM partOfSpeechVocabulary"):
			self.posses[row["value"]] = row["id"]


	def setLanguages(self):
		for row in self.__getRows("SELECT * FROM languageVocabulary"):
			self.languages[row["iso_639_1"]] = row["id"]


	def setProperties(self):
		for row in self.__getRows("SELECT * FROM propertyVocabulary"):
			key = self.__getUrlPart(row["property"]) + ":" + self.__getUrlPart(row["value"])
			self.properties[key] = row["id"]


	def setEntryRelations(self):
		for row in self.__getRows("SELECT * FROM relationVocabulary"):
			key = "lexinfo:" + self.__getUrlPart(row["relation"])
			self.entryrelations[key] = row["relationID"]


	def setSenseRelations(self):
		""" Should not be manual, but for now there is validation. """
		self.senserelations.extend( ["ontolex:reference"] )
		self.senserelations.extend( ["skos:broader", "skos:related", "skos:exactMatch"] )
		self.senserelations.extend( ["skos-thes:broaderInstantial", "skos-thes:broaderPartitive"] )
		self.senserelations.extend( ["lexinfo:antonym"] )


	def setLexicalEntries(self):
		query = "SELECT lexicalEntryID, class, pos.value AS pos_value, lex.identifier AS lex_identifier FROM lexicalEntry AS lex \
			LEFT JOIN partOfSpeechVocabulary AS pos ON lex.partOfSpeechID = pos.id"
		self.lexicalEntries = self.__getRows(query)


	def setLexicalEntry(self,lexicalEntryID):
		query = "SELECT lexicalEntryID, class, pos.value AS pos_value, identifier AS lex_identifier FROM lexicalEntry AS lex \
			LEFT JOIN partOfSpeechVocabulary AS pos ON lex.partOfSpeechID = pos.id \
			WHERE lexicalEntryID = %s"
		self.lexicalEntries = self.__getRows(query,(lexicalEntryID))


	def setLexicalEntryRelations(self):
		query = "SELECT lex.identifier AS lex_identifier, entryrel.reference, vocab.relation FROM lexicalEntryRelation AS entryrel \
			LEFT JOIN lexicalEntry AS lex ON entryrel.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN relationVocabulary AS vocab ON entryrel.relationID = vocab.relationID"
		self.lexicalEntryRelations = self.__getRows(query)


	def setLexicalEntryRelationsByID(self,lexicalEntryID):
		query = "SELECT lex.identifier AS lex_identifier, entryrel.reference, vocab.relation FROM lexicalEntryRelation AS entryrel \
			LEFT JOIN lexicalEntry AS lex ON entryrel.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN relationVocabulary AS vocab ON entryrel.relationID = vocab.relationID \
			WHERE entryrel.lexicalEntryID = %s"
		self.lexicalEntryRelations = self.__getRows(query,(lexicalEntryID))


	def setLexicalForms(self,lang_id):
		query = "SELECT form.lexicalEntryID, form.lexicalFormID, type, rep.value AS rep_value, lex.identifier AS lex_identifier, form.identifier AS form_identifier, rep.syllableCount AS syllableCount FROM lexicalForm AS form \
			LEFT JOIN lexicalEntry AS lex ON form.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN writtenRep AS rep ON form.lexicalFormID = rep.lexicalFormID \
			WHERE rep.languageID = %s"
		self.lexicalForms = self.__getRows(query,(lang_id))


	def setLexicalForm(self,lexicalEntryID,lang_id):
		query = "SELECT form.lexicalEntryID, form.lexicalFormID, type, rep.value AS rep_value, lex.identifier AS lex_identifier, form.identifier AS form_identifier, rep.syllableCount AS syllableCount FROM lexicalForm AS form \
			LEFT JOIN lexicalEntry AS lex ON form.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN writtenRep AS rep ON form.lexicalFormID = rep.lexicalFormID \
			WHERE form.lexicalEntryID = %s \
			AND rep.languageID = %s"
		self.lexicalForms.extend(self.__getRows(query,(lexicalEntryID,lang_id)))


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
		query = "SELECT form.identifier AS form_identifier, vocab.property, vocab.value FROM formProperties AS formprop \
			LEFT JOIN lexicalForm AS form ON formprop.lexicalFormID = form.lexicalFormID \
			LEFT JOIN propertyVocabulary AS vocab ON formprop.propertyID = vocab.id"
		self.lexicalProperties = self.__getRows(query)


	def setLexicalFormPropertiesByID(self):
		for form in self.lexicalForms:
			query = "SELECT form.identifier AS form_identifier, vocab.property, vocab.value FROM formProperties AS formprop \
				LEFT JOIN lexicalForm AS form ON formprop.lexicalFormID = form.lexicalFormID \
				LEFT JOIN propertyVocabulary AS vocab ON formprop.propertyID = vocab.id \
				WHERE formprop.lexicalFormID = %s"
			self.lexicalProperties.extend(self.__getRows(query,(form["lexicalFormID"])))


	def setLexicalSenses(self):
		query = "SELECT sense.lexicalSenseID, sense.lexicalEntryID, lex.identifier AS lex_identifier, sense.identifier AS sense_identifier FROM lexicalSense AS sense \
			LEFT JOIN lexicalEntry AS lex ON sense.lexicalEntryID = lex.lexicalEntryID"
		self.lexicalSenses = self.__getRows(query)


	def setLexicalSensesByID(self,lexicalEntryID):
		query = "SELECT sense.lexicalSenseID, sense.lexicalEntryID, lex.identifier AS lex_identifier, sense.identifier AS sense_identifier FROM lexicalSense AS sense \
			LEFT JOIN lexicalEntry AS lex ON sense.lexicalEntryID = lex.lexicalEntryID \
			WHERE sense.lexicalEntryID = %s"
		self.lexicalSenses.extend(self.__getRows(query,(lexicalEntryID)))


	def setLexicalSensesByEntries(self):
		for entry in self.lexicalEntries:
			self.setLexicalSensesByID(entry["lexicalEntryID"])


	def setSenseDefinitions(self,lang_id):
		""" Definition is optional."""
		for sense in self.lexicalSenses:
			query = "SELECT value FROM senseDefinition WHERE lexicalSenseID = %s AND languageID = %s"
			row = self.__getRow(query,(sense["lexicalSenseID"],lang_id))
			if row:
				self.lexicalSenseDefinitions[sense["sense_identifier"]] = row["value"]


	def setSenseReferences(self):
		query = "SELECT sense.identifier AS sense_identifier, namespace, property, reference FROM senseReference \
			LEFT JOIN lexicalSense AS sense ON senseReference.lexicalSenseID = sense.lexicalSenseID"
		self.senseReferences = self.__getRows(query)


	def setSenseReferencesByID(self):
		for sense in self.lexicalSenses:
			query = "SELECT sense.identifier AS sense_identifier, namespace, property, reference FROM senseReference \
				LEFT JOIN lexicalSense AS sense ON senseReference.lexicalSenseID = sense.lexicalSenseID \
				WHERE senseReference.lexicalSenseID = %s"
			self.senseReferences.extend(self.__getRows(query,(sense["lexicalSenseID"])))


	def setLexicalComponents(self):
		query = "SELECT lex.identifier AS lex_identifier, comp.identifier AS comp_identifier, position FROM lexicalEntryComponent AS lexcomp \
			LEFT JOIN lexicalEntry AS lex ON lexcomp.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN component AS comp ON lexcomp.componentID = comp.componentID"
		self.lexicalEntryComponents.extend(self.__getRows(query))


	def setLexicalComponentsByID(self,lexicalEntryID):
		query = "SELECT lex.identifier AS lex_identifier, comp.identifier AS comp_identifier, position FROM lexicalEntryComponent AS lexcomp \
			LEFT JOIN lexicalEntry AS lex ON lexcomp.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN component AS comp ON lexcomp.componentID = comp.componentID \
			WHERE lexcomp.lexicalEntryID = %s"
		self.lexicalEntryComponents.extend(self.__getRows(query,(lexicalEntryID)))


	def setComponents(self):
		query = "SELECT DISTINCT comp.identifier AS comp_identifier, lex.identifier AS lex_identifier, form.identifier AS form_identifier FROM component AS comp \
			LEFT JOIN lexicalEntry AS lex ON comp.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN lexicalForm AS form ON comp.lexicalFormID = form.lexicalFormID"
		self.components.extend(self.__getRows(query))


	def setComponentsByID(self,lexicalEntryID,lang_id):
		query = "SELECT DISTINCT comp.identifier AS comp_identifier, lex.identifier AS lex_identifier, form.identifier AS form_identifier, rep.value AS rep_value FROM component AS comp \
			LEFT JOIN lexicalEntryComponent AS lexcomp ON comp.componentID = lexcomp.componentID \
			LEFT JOIN lexicalEntry AS lex ON comp.lexicalEntryID = lex.lexicalEntryID \
			LEFT JOIN lexicalForm AS form ON comp.lexicalFormID = form.lexicalFormID \
			LEFT JOIN writtenRep AS rep ON form.lexicalFormID = rep.lexicalFormID \
			WHERE lexcomp.lexicalEntryID = %s \
			AND rep.languageID = %s"
		self.components.extend(self.__getRows(query,(lexicalEntryID,lang_id)))


	def getLexicalEntryID(self,value,partOfSpeechID):
		query = "SELECT lexicalEntryID FROM lexicalEntry WHERE value = %s AND partOfSpeechID = %s"
		row = self.__getRow(query,(value,partOfSpeechID))
		return row["lexicalEntryID"]


	def getLexicalSenseID(self,lexicalEntryID):
		query = "SELECT lexicalSenseID FROM lexicalSense WHERE lexicalEntryID = %s"
		row = self.__getRow(query,(lexicalEntryID))
		return row["lexicalSenseID"]


	def getID(self,identifier,table):
		""" Return the real database ID from either entry, form or sense, based on identifier. """
		field = table + "ID"
		query = "SELECT " + field + " FROM " + table + " WHERE identifier = %s"
		row = self.__getRow(query,(identifier))
		return row[field]


	def getCountlexicalSenses(self,lexicalEntryID):
		query = "SELECT count(*) AS count FROM lexicalSense WHERE lexicalEntryID = %s"
		row = self.__getRow(query,(lexicalEntryID))
		return int(row["count"])


	def checkSenseReferenceExists(self,lexicalSenseID,relation,reference):
		namespace = relation.split(":")[0]
		property = relation.split(":")[1]
		query = "SELECT * FROM senseReference WHERE lexicalSenseID = %s AND namespace = %s AND property = %s AND reference = %s"
		row = self.__getRow(query,(lexicalSenseID,namespace,property,reference))
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
			self.insertFormProperty(lexicalFormID,self.properties[property])
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
		query = "SELECT lexicalEntryID FROM lexicalForm WHERE lexicalFormID = %s"
		row = self.__getRow(query,(lexicalFormID))

		if row:
			return self.insertComponent(row["lexicalEntryID"],lexicalFormID,True)
		else:
			return "failed"


	def findLexicalEntry(self,word,pos_id):
		query = "SELECT lexicalEntryID FROM lexicalEntry WHERE value = %s AND partOfSpeechID = %s"
		row = self.__getRow(query,(word,pos_id))

		if row:
			return row["lexicalEntryID"]
		else:
			return None


	def findlexicalForm(self,lexicalEntryID,word,lang_id):
		query = "SELECT form.lexicalFormID FROM lexicalForm AS form \
			LEFT JOIN writtenRep AS rep ON form.lexicalFormID = rep.lexicalFormID \
			WHERE form.lexicalEntryID = %s \
			AND rep.value = %s \
			AND rep.languageID = %s"
		row = self.__getRow(query,(lexicalEntryID,word,lang_id))

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


	def insertLexicalEntryRelation(self,lexicalEntryID,relationID,reference,commit=False):
		c = self.DB.cursor()
		query = "INSERT INTO lexicalEntryRelation (lexicalEntryID,relationID,reference) VALUES (%s,%s,%s)"
		c.execute(query, (lexicalEntryID,relationID,reference))
		c.close()
		if commit:
			self.DB.commit()


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


	def insertFormProperty(self,lexicalFormID,propertyID,commit=False):
		c = self.DB.cursor()
		query = "INSERT INTO formProperties (lexicalFormID,propertyID) VALUES (%s,%s)"
		c.execute(query, (lexicalFormID,propertyID))
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


	def updateLexicalEntryValue(self,lexicalEntryID,label,languageID):
		c = self.DB.cursor()

		# find canonicalForm
		query = "SELECT * FROM lexicalForm WHERE lexicalEntryID = %s AND type = 'canonicalForm'"
		c.execute(query, (lexicalEntryID))
		canonicalform = c.fetchone()

		# update entry and writtenrep
		query = "UPDATE lexicalEntry SET value = %s WHERE lexicalEntryID = %s"
		c.execute(query, (label,lexicalEntryID))
		query = "UPDATE writtenRep SET value = %s WHERE lexicalFormID = %s AND languageID = %s"
		c.execute(query,(label,canonicalform["lexicalFormID"],languageID))

		self.DB.commit()


	def updateSyllableCount(self,lexicalFormID,syllableCount,languageID):
		c = self.DB.cursor()
		query = "UPDATE writtenRep SET syllableCount = %s WHERE lexicalFormID = %s AND languageID = %s"
		c.execute(query,(syllableCount,lexicalFormID,languageID))
		c.close()
		self.DB.commit()


	def __getRow(self,query,args=None):
		c = self.DB.cursor()
		c.execute(query,args)
		row = c.fetchone()
		c.close()
		return row


	def __getRows(self,query,args=None):
		c = self.DB.cursor()
		c.execute(query,args)
		rows = c.fetchall()
		c.close()
		return rows


	def __getUrlPart(self,url):
		""" Helper function to get the last part of the property url."""
		parsed = urlparse(url)
		if parsed.fragment:
			return parsed.fragment
		else:
			return parsed.path.split('/')[-1]
