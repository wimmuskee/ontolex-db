# -*- coding: utf-8 -*-
# This script takes a csv with: metal names, and adds the massNoun property,
# and neuter property (if nl). Also makes sure the hypernym is set.
# For some, a adjective might be set.

from rulesets.scripts.script import ScriptCommon
from format.namespace import LEXINFO, ONTOLEX
import csv
from rdflib import URIRef

class Script(ScriptCommon):
	def __init__(self,config,language,dont_ask=False):
		ScriptCommon.__init__(self,config,language,dont_ask)
		self.setHypernym("http://www.wikidata.org/entity/Q11426")

		with open('custom-csv/metals.csv', 'r') as csvfile:
			spamreader = csv.reader(csvfile, delimiter=',')
			for row in spamreader:
				self.processRow(row[0],row[1])


	def processRow(self,name,adjective):
		self.__resetData()

		# canonicals
		self.setCanonical(name,"noun","name")
		self.setCanonical(adjective,"adjective","adjective")

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


	def __resetData(self):
		self.data = { 
			"name": { "lexicalEntryID": "", "senseCount": 0, "sense_id": -1, "lexicalSenseID": "" },
			"adjective": { "lexicalEntryID": "", "senseCount": 0, "sense_id": -1, "lexicalSenseID": "" }
			}
