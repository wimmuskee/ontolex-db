# -*- coding: utf-8 -*-
# This script takes a csv with: country names,country adjectives,inhabitant names
# and adds them to the lexicon with the proper relations if they do not exist already,
# for example,
#  - country_name "Germany" noun, hypernym "country"
#  - country_adjective "German" adjective, pertainsTo country_name
#  - inhabitant_name "German" noun, relatedTerm country_name

from rulesets.ruleset import RulesetCommon
from format.namespace import LEXINFO, ONTOLEX
import csv
from rdflib import URIRef

class CustomRuleset(RulesetCommon):
	def __init__(self,config,language,dont_ask=False):
		RulesetCommon.__init__(self,config,dont_ask)
		self.language = language
		self.lang_id = self.db.languages[language]

		with open('custom-csv/countries.csv', 'r') as csvfile:
			spamreader = csv.reader(csvfile, delimiter=',')
			for row in spamreader:
				self.processRow(row[0],row[1],row[2])


	def processRow(self,name,adjective,inhabitant):
		self.__resetData()

		# canonicals
		self.__setCanonical(name,"noun","name")
		self.__setCanonical(adjective,"adjective","adjective")
		self.__setCanonical(inhabitant,"noun","inhabitant")

		# pertainsTo
		if self.__checkSense("name") and self.__checkSense("adjective"):
			self.__setSense("name")
			self.__setSense("adjective")
			if not (URIRef(self.data["adjective"]["lexicalSenseID"]),LEXINFO.pertainsTo,URIRef(self.data["name"]["lexicalSenseID"])) in self.g:
				if self.userCheck("add pertainsTo",name,adjective):
					self.db.insertSenseReference(self.data["adjective"]["sense_id"],"lexinfo:pertainsTo",self.data["name"]["lexicalSenseID"],True)

		# relatedTerm
		if self.__checkSense("name") and self.__checkSense("inhabitant"):
			self.__setSense("name")
			self.__setSense("inhabitant")
			if not (URIRef(self.data["inhabitant"]["lexicalSenseID"]),LEXINFO.relatedTerm,URIRef(self.data["name"]["lexicalSenseID"])) in self.g:
				if self.userCheck("add relatedTerm",name,inhabitant):
					self.db.insertSenseReference(self.data["inhabitant"]["sense_id"],"lexinfo:relatedTerm",self.data["name"]["lexicalSenseID"],True)


	def __setCanonical(self,value,pos,key):
		if not value:
			return

		lexicalEntryID = self.findLexicalEntry(value,URIRef(LEXINFO + pos))
		if not lexicalEntryID and self.userCheck("add canonical",value,pos):
				lexid = self.db.storeCanonical(value,self.lang_id,self.db.posses[pos],False)
				lexicalEntryID = self.db.getIdentifier(lexid,"lexicalEntry")

		if lexicalEntryID:
			self.data[key]["lexicalEntryID"] = lexicalEntryID
			self.data[key]["senseCount"] = self.countLexicalSenses(lexicalEntryID)


	def __setSense(self,key):
		""" Sets sense_id by retrieving it if it exists, or inserting if not. """
		if self.data[key]["lexicalSenseID"]:
			return

		if self.data[key]["senseCount"] == 1:
			lexicalSenseID = str(self.g.value(URIRef(self.data[key]["lexicalEntryID"]),ONTOLEX.sense,None))
			self.data[key]["sense_id"] = self.db.getID(lexicalSenseID,"lexicalSense")
			self.data[key]["lexicalSenseID"] = lexicalSenseID
		else:
			entry_id = self.db.getID(self.data[key]["lexicalEntryID"],"lexicalEntry")
			self.data[key]["sense_id"] = self.db.insertLexicalSense(entry_id,True)
			self.data[key]["lexicalSenseID"] = self.db.getIdentifier(self.data[key]["sense_id"],"lexicalSense")


	def __checkSense(self,key):
		"""Checks whether lexicalEntryID for key is present and senseCount
		is lower than 2."""
		if self.data[key]["lexicalEntryID"] and self.data[key]["senseCount"] < 2:
			return True
		else:
			return False


	def __resetData(self):
		self.data = { 
			"name": { "lexicalEntryID": "", "senseCount": 0, "sense_id": -1, "lexicalSenseID": "" },
			"adjective": { "lexicalEntryID": "", "senseCount": 0, "sense_id": -1, "lexicalSenseID": "" },
			"inhabitant": { "lexicalEntryID": "", "senseCount": 0, "sense_id": -1, "lexicalSenseID": "" }
			}
