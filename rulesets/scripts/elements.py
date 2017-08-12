# -*- coding: utf-8 -*-
# This script takes a csv with: element names, and adds the massNoun property,
# and neuter property (if nl). Also makes sure the hypernym is set.

from rulesets.scripts.script import ScriptCommon
from format.namespace import LEXINFO, ONTOLEX
import csv
from rdflib import URIRef

class Script(ScriptCommon):
	def __init__(self,config,language,dont_ask=False):
		ScriptCommon.__init__(self,config,language,dont_ask)
		self.setHypernym("http://www.wikidata.org/entity/Q11344")

		with open('custom-csv/elements.csv', 'r') as csvfile:
			spamreader = csv.reader(csvfile, delimiter=',')
			for row in spamreader:
				self.processRow(row[0])


	def processRow(self,name):
		self.__resetData()
		self.setCanonical(name,"noun","name")

		# name form
		canonicalFormID = self.g.value(URIRef(self.data["name"]["lexicalEntryID"]),ONTOLEX.canonicalForm,None)
		canonical_form_id = self.db.getID(str(canonicalFormID),"lexicalForm")

		# massNoun, don't ask
		if not (canonicalFormID,LEXINFO.number,LEXINFO.massNoun) in self.g:
			self.db.insertFormProperty(canonical_form_id,self.db.properties["number:massNoun"],True)

		# neuter (language specific)
		if self.language == "nl":
			if not (canonicalFormID,LEXINFO.gender,LEXINFO.neuter) in self.g and self.userCheck("add gender",name,"neuter"):
				self.db.insertFormProperty(canonical_form_id,self.db.properties["gender:neuter"],True)

		# hypernym
		if self.hypernym_senseID and self.checkSense("name"):
			self.setSense("name")
			if not (URIRef(self.data["name"]["lexicalSenseID"]),LEXINFO.hypernym,URIRef(self.hypernym_senseID)) in self.g:
				if self.userCheck("add hypernym",name,self.hypernym_label):
					self.db.insertSenseReference(self.data["name"]["sense_id"],"lexinfo:hypernym",self.hypernym_senseID,True)


	def __resetData(self):
		self.data = { "name": { "lexicalEntryID": "", "senseCount": 0, "sense_id": -1, "lexicalSenseID": "" } }
