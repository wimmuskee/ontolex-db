# -*- coding: utf-8 -*-
# This script takes a csv with: country names,country adjectives,inhabitant names
# and adds them to the lexicon with the proper relations if they do not exist already,
# for example,
#  - country_name "Germany" noun, massNoun, hypernym "country"
#  - country_adjective "German" adjective, pertainsTo country_name
#  - inhabitant_name "German" noun, relatedTerm country_name

from rulesets.scripts.script import ScriptCommon
from format.namespace import LEXINFO, ONTOLEX
import csv
from rdflib import URIRef

class Script(ScriptCommon):
	def __init__(self,config,language,dont_ask=False):
		ScriptCommon.__init__(self,config,language,dont_ask)
		self.setHypernym("http://www.wikidata.org/entity/Q6256")

		with open('custom-csv/countries.csv', 'r') as csvfile:
			spamreader = csv.reader(csvfile, delimiter=',')
			for row in spamreader:
				self.processRow(row[0],row[1],row[2])


	def processRow(self,name,adjective,inhabitant):
		self.__resetData()

		# canonicals
		self.setCanonical(name,"noun","name")
		self.setCanonical(adjective,"adjective","adjective")
		self.setCanonical(inhabitant,"noun","inhabitant")

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

		# pertainsTo
		if self.checkSense("name") and self.checkSense("adjective"):
			self.setSense("name")
			self.setSense("adjective")
			if not (URIRef(self.data["adjective"]["lexicalSenseID"]),LEXINFO.pertainsTo,URIRef(self.data["name"]["lexicalSenseID"])) in self.g:
				if self.userCheck("add pertainsTo",name,adjective):
					self.db.insertSenseReference(self.data["adjective"]["sense_id"],"lexinfo:pertainsTo",self.data["name"]["lexicalSenseID"],True)

		# relatedTerm
		if self.checkSense("name") and self.checkSense("inhabitant"):
			self.setSense("name")
			self.setSense("inhabitant")
			if not (URIRef(self.data["inhabitant"]["lexicalSenseID"]),LEXINFO.relatedTerm,URIRef(self.data["name"]["lexicalSenseID"])) in self.g:
				if self.userCheck("add relatedTerm",name,inhabitant):
					self.db.insertSenseReference(self.data["inhabitant"]["sense_id"],"lexinfo:relatedTerm",self.data["name"]["lexicalSenseID"],True)


	def __resetData(self):
		self.data = { 
			"name": { "lexicalEntryID": "", "senseCount": 0, "sense_id": -1, "lexicalSenseID": "" },
			"adjective": { "lexicalEntryID": "", "senseCount": 0, "sense_id": -1, "lexicalSenseID": "" },
			"inhabitant": { "lexicalEntryID": "", "senseCount": 0, "sense_id": -1, "lexicalSenseID": "" }
			}
