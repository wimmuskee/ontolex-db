# -*- coding: utf-8 -*-

from database.mysql import Database
from rdflib import Graph
from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import SKOS, RDFS, RDF, XSD
from rdflib.plugins.sparql import prepareQuery

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
		global DECOMP
		global LIME

		ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
		LEXINFO = Namespace("http://www.lexinfo.net/ontology/2.0/lexinfo#")
		DECOMP = Namespace("http://www.w3.org/ns/lemon/decomp#")
		LIME = Namespace("http://www.w3.org/ns/lemon/lime#")

		self.g = Graph()
		self.g.parse("export.ttl", format="turtle")
		self.g.bind("ontolex", ONTOLEX)
		self.g.bind("lexinfo", LEXINFO)
		self.g.bind("decomp", DECOMP)
		# later, check if language is correct
		# lexicon definition with lime language
		# later also check on first lexical entry rdfs language

		self.dont_ask = dont_ask

		# store lexicalForms, ID is key, value label
		self.lexicalEntries = {}
		# store lexicalForms, ID is key, value is dict with label and lexicalEntryID
		self.lexicalForms = {}


	def nounComponents(self,componentID):
		""" Try to match a component to a postfix on nouns."""
		searchterm = self.getLabel(componentID)
		searchtermCount = len(searchterm)

		# only add those entries that postfix match on the searchterm, and do not have a match to the component.
		for lexicalEntryID in self.g.subjects(LEXINFO.partOfSpeech,LEXINFO.noun):
			label = self.getLabel(lexicalEntryID)
			if len(label) > searchtermCount and label[-searchtermCount:] == searchterm:
				if not (URIRef(lexicalEntryID),DECOMP.constituent,URIRef(componentID)) in self.g:
					self.lexicalEntries[str(lexicalEntryID)] = label

		# now see if we can find a match for the prefix
		for lexicalEntryID in self.lexicalEntries:
			label = self.lexicalEntries[lexicalEntryID]
			prefix = label[:-searchtermCount]
			
			if (None,ONTOLEX.writtenRep,Literal(prefix, lang=self.language)) in self.g:
				# for each found form, we need to ask to add the specific form and entry
				for lexicalFormID in self.g.subjects(ONTOLEX.writtenRep,Literal(prefix, lang=self.language)):
					formEntryID = self.g.value(None,ONTOLEX.lexicalForm,URIRef(lexicalFormID))
					formEntryPos = self.g.value(URIRef(formEntryID),LEXINFO.partOfSpeech,None)
					
					if self.userCheck("components", label, prefix + " - " + str(formEntryPos)[44:]):
						form_id = self.db.getID(str(lexicalFormID),"lexicalForm")
						entry_id = self.db.getID(str(formEntryID),"lexicalEntry")
						post_comp_id = self.db.getID(componentID,"component")
						base_entry_id = self.db.getID(str(lexicalEntryID),"lexicalEntry")
						pre_comp_id = self.db.insertComponent(entry_id,form_id,True)
						self.db.insertLexicalEntryComponent(base_entry_id,pre_comp_id,1)
						self.db.insertLexicalEntryComponent(base_entry_id,post_comp_id,2,True)
			else:
				print("prefix not found as writtenRep: " + prefix)


	def refreshComponents(self):
		components = self.getTopUsedComponents()
		for c in components:
			self.nounComponents(c)
			self.lexicalEntries = {}


	def nounComponentsSenses(self):
		"""For each component, find used compounds and see if they are narrower in meaning."""
		self.setQuery("countSenses")
		
		components = self.getTopUsedComponents()
		for componentID in components:
			componentLexicalEntryID = self.g.value(URIRef(componentID),DECOMP.correspondsTo,None)
			#lex_id = self.db.getID(lexicalEntryID,"lexicalEntry")
			componentLabel = self.getLabel(componentLexicalEntryID)
			componentSenseCount = int(self.g.query(self.q_countSenses, initBindings={'lexicalEntryID': URIRef(componentLexicalEntryID)}).bindings[0]["?count"])
			if componentSenseCount != 1:
				print("either too few or too many senses (" + str(componentSenseCount) + "): " + componentLabel)
				continue
			else:
				targetSenseID = str(self.g.value(URIRef(componentLexicalEntryID),ONTOLEX.sense,None))

				# find compounds and their senses
				for compoundLexicalEntryID in self.g.subjects(DECOMP.constituent,URIRef(componentID)):
					compoundLabel = self.getLabel(compoundLexicalEntryID)
					compound_lex_id = self.db.getID(compoundLexicalEntryID,"lexicalEntry")
					compoundSenseCount = int(self.g.query(self.q_countSenses, initBindings={'lexicalEntryID': URIRef(compoundLexicalEntryID)}).bindings[0]["?count"])
					if compoundSenseCount == 0:
						if self.userCheck("add sense", "compoundword", compoundLabel):
							compound_sense_id = self.db.insertLexicalSense(compound_lex_id,True)
						else:
							continue
					elif compoundSenseCount == 1:
						# check if relation exists
						compoundLexicalSenseID = self.g.value(URIRef(compoundLexicalEntryID),ONTOLEX.sense,None)
						if (URIRef(compoundLexicalSenseID),SKOS.broader,URIRef(targetSenseID)) in self.g:
							print("relation exists: " + compoundLabel)
							continue
						compound_sense_id = self.db.getLexicalSenseID(compound_lex_id)
					else:
						print("target has multiple senses: " + compoundLabel)
						continue

					# we have a compound_sense_id, so we can add the relation
					if self.userCheck("add broader", componentLabel, compoundLabel):
						self.db.insertSenseReference(compound_sense_id,"skos:broader",targetSenseID,True)


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


	# we have this in prepared form, but not sure which version i will use
	def countLexicalenses(self,lexicalEntryIdentifier):
		c = 0
		for lexicalSenseIdentifier in self.g.objects(URIRef(lexicalEntryIdentifier),ONTOLEX.sense):
			c = c + 1
		return c


	def setQuery(self,query):
		""" Set prepared queries. """
		if query == "countSenses":
			self.q_countSenses = prepareQuery("""SELECT (count(*) as ?count) WHERE { ?lexicalEntryID ontolex:sense ?o }""", initNs = {"ontolex": ONTOLEX})


	def getTopUsedComponents(self,min_threshold=2):
		components = {}
		result = self.g.query( """SELECT ?componentID (COUNT(?componentID) as ?countComponentID) WHERE {
			?lexicalEntry decomp:constituent ?componentID . }
			GROUP BY ?componentID
			ORDER BY desc(?countComponentID)""")

		for row in result:
			componentID = str(row[0])
			count = int(row[1])
			if count > min_threshold:
				components[componentID] = count

		return components

