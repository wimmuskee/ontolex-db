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
		self.db.setProperties()
		self.db.setEntryRelations()

		global ONTOLEX
		global LEXINFO
		global DECOMP
		global ISOCAT
		global SKOSTHES
		global LIME

		ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
		LEXINFO = Namespace("http://www.lexinfo.net/ontology/2.0/lexinfo#")
		DECOMP = Namespace("http://www.w3.org/ns/lemon/decomp#")
		ISOCAT = Namespace("http://www.isocat.org/datcat/")
		SKOSTHES = Namespace("http://purl.org/iso25964/skos-thes#")
		LIME = Namespace("http://www.w3.org/ns/lemon/lime#")

		self.g = Graph()
		self.g.parse("export.ttl", format="turtle")
		self.g.bind("ontolex", ONTOLEX)
		self.g.bind("lexinfo", LEXINFO)
		self.g.bind("decomp", DECOMP)
		self.g.bind("skosthes", SKOSTHES)
		self.g.bind("isocat", ISOCAT)

		# later, check if language is correct
		# lexicon definition with lime language
		# later also check on first lexical entry rdfs language

		self.dont_ask = dont_ask

		# store lexicalEntries, ID is key, value meta dict
		self.lexicalEntries = {}
		# store lexicalForms, ID is key, value is dict with label and lexicalEntryID
		self.lexicalForms = {}


	def setWordDbFile(self,filepath):
		with open(filepath) as f:
			self.worddb = set(f.read().splitlines())


	def nounComponents(self,componentID):
		""" Try to match a component to a postfix on nouns."""
		searchterm = self.getLabel(componentID)
		print(searchterm)
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


	def verbComponents(self,componentID):
		""" Try to match a component to a prefix on verbs."""
		searchterm = self.getLabel(componentID)
		searchtermCount = len(searchterm)

		# 1. collect verbs
		self.setLexicalEntriesByPOS(LEXINFO.verb,["label"])

		# 2. delete entries that do not start with searchterm, and do not have components set
		for lexicalEntryID in list(self.lexicalEntries):
			label = self.lexicalEntries[lexicalEntryID]["label"]
			if len(label) <= searchtermCount or label[:searchtermCount] != searchterm:
				del(self.lexicalEntries[lexicalEntryID])
				continue
			elif (URIRef(lexicalEntryID),DECOMP.constituent,URIRef(componentID)) in self.g:
				del(self.lexicalEntries[lexicalEntryID])

		# 3. now see if we can find a match for the postfix (in verbs)
		for lexicalEntryID in list(self.lexicalEntries):
			label = self.lexicalEntries[lexicalEntryID]["label"]
			postfix = label[searchtermCount:]
			self.lexicalEntries[lexicalEntryID]["match"] = {}

			for lexicalFormID in self.g.subjects(ONTOLEX.writtenRep,Literal(postfix, lang=self.language)):
				if (URIRef(lexicalFormID),LEXINFO.verbFormMood,LEXINFO.infinitive) in self.g:
					self.lexicalEntries[lexicalEntryID]["match"] = { "lexicalFormID": str(lexicalFormID), "value": postfix, "lexicalEntryID": str(self.g.value(None,ONTOLEX.lexicalForm,URIRef(lexicalFormID)))}

			if not self.lexicalEntries[lexicalEntryID]["match"]:
				del(self.lexicalEntries[lexicalEntryID])

		# 4. ask and store matches
		for lexicalEntryID,meta in self.lexicalEntries.items():
			if self.userCheck("components", meta["label"], searchterm + " + " + meta["match"]["value"]):
				source_entry_id = self.db.getID(lexicalEntryID,"lexicalEntry")
				target_entry_id = self.db.getID(meta["match"]["lexicalEntryID"],"lexicalEntry")
				target_form_id = self.db.getID(meta["match"]["lexicalFormID"],"lexicalForm")
				pre_comp_id = self.db.getID(componentID,"component")
				post_comp_id = self.db.insertComponent(target_entry_id,target_form_id,True)
				self.db.insertLexicalEntryComponent(source_entry_id,pre_comp_id,1)
				self.db.insertLexicalEntryComponent(source_entry_id,post_comp_id,2,True)


	def nounComponentsSenses(self):
		print("first redesign")
		exit()
		"""For each component, find used compounds and see if they are narrower in meaning."""
		self.setQuery("countSenses")
		
		components = self.getTopUsedComponents()
		for componentID in components:
			componentLexicalEntryID = self.g.value(URIRef(componentID),DECOMP.correspondsTo,None)
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


	def verbInfinitives(self):
		""" Set verbFormMood infinitive for all verb canonicals. """
		result = self.g.query("""SELECT ?lexicalFormID WHERE {
			?lexicalEntryID rdf:type ontolex:LexicalEntry ;
				lexinfo:partOfSpeech lexinfo:verb ;
				ontolex:canonicalForm ?lexicalFormID .
			MINUS { ?lexicalFormID lexinfo:verbFormMood lexinfo:infinitive } }""")
		for row in result:
			lexicalFormID = str(row[0])
			form_id = self.db.getID(lexicalFormID,"lexicalForm")
			self.db.insertFormProperty(form_id,self.db.properties["verbFormMood:infinitive"],True)


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


	def setLexicalEntriesByPOS(self,partOfSpeech,fieldset=[]):
		for lexicalEntryID in self.g.subjects(LEXINFO.partOfSpeech,partOfSpeech):
			lexicalEntryID = str(lexicalEntryID)
			self.lexicalEntries[lexicalEntryID] = {}
			if "label" in fieldset:
				self.lexicalEntries[lexicalEntryID]["label"] = self.getLabel(lexicalEntryID)
			if "senses" in fieldset:
				self.lexicalEntries[lexicalEntryID]["senses"] = self.getLexicalSenseIDs(lexicalEntryID)
			if "forms" in fieldset:
				self.lexicalEntries[lexicalEntryID]["forms"] = self.getLexicalFormIDs(lexicalEntryID)


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


	def getLabel(self,identifier):
		return str(self.g.value(URIRef(identifier),RDFS.label,None))


	def getLexicalFormIDs(self,lexicalEntryID):
		formIDs = []
		for lexicalFormID in self.g.objects(URIRef(lexicalEntryID),ONTOLEX.lexicalForm):
			formIDs.append(str(lexicalFormID))
		return formIDs


	def getLexicalSenseIDs(self,lexicalEntryID):
		senseIDs = []
		for lexicalSenseID in self.g.objects(URIRef(lexicalEntryID),ONTOLEX.sense):
			senseIDs.append(str(lexicalSenseID))
		return senseIDs


	def filterEntriesRemoveComponentBased(self):
		""" Remove all entries that are made from components. """
		for lexicalEntryID in list(self.lexicalEntries):
			if (URIRef(lexicalEntryID),DECOMP.constituent,None) in self.g:
				del(self.lexicalEntries[lexicalEntryID])


	def filterEntriesOnlyComponentBased(self):
		""" Keep all entries that are made from components. """
		for lexicalEntryID in list(self.lexicalEntries):
			if not (URIRef(lexicalEntryID),DECOMP.constituent,None) in self.g:
				del(self.lexicalEntries[lexicalEntryID])


	def checkLexicalEntryExists(self,word,partOfSpeech):
		for lexicalEntryIdentifier in self.g.subjects(LEXINFO.partOfSpeech,partOfSpeech):
			if (URIRef(lexicalEntryIdentifier),RDFS.label,Literal(word, lang=self.language)) in self.g:
				return True
		return False


	def findLexicalEntry(self,word,partOfSpeech):
		lexicalEntryID = ""
		for lexicalEntryIdentifier in self.g.subjects(LEXINFO.partOfSpeech,partOfSpeech):
			if (URIRef(lexicalEntryIdentifier),RDFS.label,Literal(word, lang=self.language)) in self.g:
				lexicalEntryID = str(lexicalEntryIdentifier)
				break
		return lexicalEntryID


	def checkFormRelation(self,lexicalEntryID,checkPredicate,checkObject):
		""" Given a lexicalEntryID, check all related forms to see if the requested relation is present."""
		for lexicalFormID in self.g.objects(URIRef(lexicalEntryID),ONTOLEX.otherForm):
			if (URIRef(lexicalFormID),checkPredicate,checkObject) in self.g:
				return True
		return False


	# we have this in prepared form, but not sure which version i will use
	def countLexicalSenses(self,lexicalEntryIdentifier):
		c = 0
		for lexicalSenseIdentifier in self.g.objects(URIRef(lexicalEntryIdentifier),ONTOLEX.sense):
			c = c + 1
		return c


	def setQuery(self,query):
		""" Set prepared queries. """
		if query == "countSenses":
			self.q_countSenses = prepareQuery("""SELECT (count(*) as ?count) WHERE {
				?lexicalEntryID ontolex:sense ?o }""", initNs={"ontolex": ONTOLEX})
		if query == "getNarrowerInstantialByReference":
			self.q_getNarrowerInstantialByReference = prepareQuery( """SELECT ?lexicalEntryID WHERE { 
				?sourceLexicalSenseID ontolex:reference ?reference ;
					skosthes:narrowerInstantial ?lexicalSenseID .
				?lexicalEntryID ontolex:sense ?lexicalSenseID }""", initNs={"ontolex": ONTOLEX, "skosthes": SKOSTHES })
		if query == "askCanonicalByPOS":
			self.q_askCanonicalByPOS = q = prepareQuery( """ASK { 
				?lexicalEntryID rdf:type ontolex:LexicalEntry ;
					lexinfo:partOfSpeech ?partOfSpeech ;
					rdfs:label ?label . }""", initNs = {"ontolex": ONTOLEX, "lexinfo": LEXINFO })


	# NOTE, not used anymore, we need a better way to manage components
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
