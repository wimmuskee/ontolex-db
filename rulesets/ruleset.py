# -*- coding: utf-8 -*-

from database.mysql import Database
from rdflib import Graph
from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import SKOS, RDFS, RDF, XSD

""" The pattern all rulesets should follow.
1. select the entries we want to change
1.1 generic select on wordtype
1.2 check if intended relation does not exist in any of the desired class
"""

class RulesetCommon:
	def __init__(self,config):
		self.db = Database(config)
		self.db.connect()
		self.db.setPosses()
		self.db.setLanguages()
		self.db.setMorphoSyntactics()

		global ONTOLEX
		global LEXINFO
		global LIME
		global LANGUAGE

		ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
		LEXINFO = Namespace("http://www.lexinfo.net/ontology/2.0/lexinfo#")
		LIME = Namespace("http://www.w3.org/ns/lemon/lime#")

		self.g = Graph()
		self.g.parse("export.ttl", format="turtle")
		# later, check if language is correct
		# lexicon definition with lime language
		# later also check on first lexical entry rdfs language

		# store lexicalForms, ID is key, value is dict with label and lexicalEntryID
		self.lexicalForms = {}


	def userCheck(self,question,source,target):
		if not target:
			return False

		answer = input(question + "? " + source + " :: " + target + " ")
		if answer == "y":
			return True
		else:
			return False


	def setProcessableForms(self,partOfSpeech,checkPredicate):
		""" Use when assuming all forms should have at least a certain predicate set.
		We're trying to find those without.
		"""
		for lexicalEntryID in self.g.subjects(LEXINFO.partOfSpeech,partOfSpeech):
			for lexicalFormID in self.g.objects(URIRef(lexicalEntryID),ONTOLEX.lexicalForm):
				if not (URIRef(lexicalFormID),checkPredicate,None) in self.g:
					store = {
						"label": str(self.g.value(URIRef(lexicalFormID),ONTOLEX.writtenRep)),
						"lexicalEntryID": str(lexicalEntryID) }
					self.lexicalForms[str(lexicalFormID)] = store


	def getLexicalSenseIDsByReference(self,references):
		""" In case a relation is determined by the word being part of a certain sense group (countries for instance)."""
		lexicalSenseIDs = []
		for reference in references:
			for lexicalSenseID in self.g.subjects(ONTOLEX.reference,URIRef(reference)):
				lexicalSenseIDs.append(str(lexicalSenseID))
		return lexicalSenseIDs