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
	def __init__(self,config,dont_ask=False):
		self.db = Database(config)
		self.db.connect()
		self.db.setPosses()
		self.db.setLanguages()
		self.db.setMorphoSyntactics()

		global ONTOLEX
		global LEXINFO
		global LIME

		ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
		LEXINFO = Namespace("http://www.lexinfo.net/ontology/2.0/lexinfo#")
		LIME = Namespace("http://www.w3.org/ns/lemon/lime#")

		self.g = Graph()
		self.g.parse("export.ttl", format="turtle")
		# later, check if language is correct
		# lexicon definition with lime language
		# later also check on first lexical entry rdfs language

		self.dont_ask = dont_ask

		# store lexicalForms, ID is key, value label
		self.lexicalEntries = {}
		# store lexicalForms, ID is key, value is dict with label and lexicalEntryID
		self.lexicalForms = {}


	def userCheck(self,question,source,target):
		if not target:
			return False

		if self.dont_ask:
			return True

		answer = input(question + "? " + source + " :: " + target + " ")
		if answer == "y":
			return True
		else:
			return False


	def setProcessableEntries(self,partOfSpeech,checkPredicate,checkObject):
		""" Find entries that do not have a form with the specified relation.
		We're gonna try to find new forms with that relation. 
		"""
		for lexicalEntryID in self.g.subjects(LEXINFO.partOfSpeech,partOfSpeech):
			if self.checkFormRelation(lexicalEntryID,checkPredicate,checkObject):
				continue
			self.lexicalEntries[str(lexicalEntryID)] = self.getLabel(lexicalEntryID)


	def setProcessableForms(self,partOfSpeech,checkPredicate):
		""" Use when assuming all forms should have at least a certain predicate set.
		We're trying to find those without.
		"""
		for lexicalEntryID in self.g.subjects(LEXINFO.partOfSpeech,partOfSpeech):
			for lexicalFormID in self.g.objects(URIRef(lexicalEntryID),ONTOLEX.lexicalForm):
				if not (URIRef(lexicalFormID),checkPredicate,None) in self.g:
					store = {
						"label": self.getLabel(lexicalFormID),
						"lexicalEntryID": str(lexicalEntryID) }
					self.lexicalForms[str(lexicalFormID)] = store


	def getLexicalSenseIDsByReference(self,references):
		""" In case a relation is determined by the word being part of a certain sense group (countries for instance)."""
		lexicalSenseIDs = []
		for reference in references:
			for lexicalSenseID in self.g.subjects(ONTOLEX.reference,URIRef(reference)):
				lexicalSenseIDs.append(str(lexicalSenseID))
		return lexicalSenseIDs


	def getLabel(self,identifier):
		return str(self.g.value(URIRef(identifier),RDFS.label,None))


	def checkLexicalEntryExists(self,word,partOfSpeech):
		for lexicalEntryIdentifier in self.g.subjects(LEXINFO.partOfSpeech,partOfSpeech):
			if (URIRef(lexicalEntryIdentifier),RDFS.label,Literal(word, lang=self.language)) in self.g:
				return True
		return False

	def findLexicalEntry(self,word,partOfSpeech):
		for lexicalEntryIdentifier in self.g.subjects(LEXINFO.partOfSpeech,partOfSpeech):
			if (URIRef(lexicalEntryIdentifier),RDFS.label,Literal(word, lang=self.language)) in self.g:
				return str(lexicalEntryIdentifier)


	def checkFormRelation(self,lexicalEntryID,checkPredicate,checkObject):
		""" Given a lexicalEntryID, check all related forms to see if the requested relation is present."""
		for lexicalFormID in self.g.objects(URIRef(lexicalEntryID),ONTOLEX.otherForm):
			if (URIRef(lexicalFormID),checkPredicate,checkObject) in self.g:
				return True
		return False