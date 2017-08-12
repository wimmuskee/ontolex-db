# -*- coding: utf-8 -*-
# parent class for scripts, calls RulesetCommon as own parent class

from rulesets.ruleset import RulesetCommon
from format.namespace import LEXINFO, ONTOLEX
from rdflib import URIRef

class ScriptCommon(RulesetCommon):
	def __init__(self,config,language,dont_ask=False):
		RulesetCommon.__init__(self,config,dont_ask)
		self.language = language
		self.lang_id = self.db.languages[language]


	def setHypernym(self,reference):
		self.hypernym_senseID = str(self.g.value(None,ONTOLEX.reference,URIRef(reference)))
		if self.hypernym_senseID:
			self.hypernym_label = self.getLabel(self.hypernym_senseID)


	def setCanonical(self,value,pos,key):
		if not value:
			return

		lexicalEntryID = self.findLexicalEntry(value,URIRef(LEXINFO + pos))
		if not lexicalEntryID and self.userCheck("add canonical",value,pos):
				lexid = self.db.storeCanonical(value,self.lang_id,self.db.posses[pos],False)
				lexicalEntryID = self.db.getIdentifier(lexid,"lexicalEntry")

		if lexicalEntryID:
			self.data[key]["lexicalEntryID"] = lexicalEntryID
			self.data[key]["senseCount"] = self.countLexicalSenses(lexicalEntryID)


	def setSense(self,key):
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


	def checkSense(self,key):
		"""Checks whether lexicalEntryID for key is present and senseCount
		is lower than 2."""
		if self.data[key]["lexicalEntryID"] and self.data[key]["senseCount"] < 2:
			return True
		else:
			return False
