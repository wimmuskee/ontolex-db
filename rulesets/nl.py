# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal, Namespace
from rulesets.ruleset import RulesetCommon
from nltk.corpus import alpino
from random import randint

ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
LEXINFO = Namespace("http://www.lexinfo.net/ontology/2.0/lexinfo#")
SKOSTHES = Namespace("http://purl.org/iso25964/skos-thes#")
DECOMP = Namespace("http://www.w3.org/ns/lemon/decomp#")
ISOCAT = Namespace("http://www.isocat.org/datcat/")
LANGUAGE = "nl"


class Ruleset(RulesetCommon):
	def __init__(self,config,dont_ask=False):
		RulesetCommon.__init__(self,config,dont_ask)
		global ONTOLEX
		global LEXINFO
		global SKOSTHES
		global DECOMP
		global ISOCAT

		# for now use alpino, we should be able to configure this
		self.worddb = set(alpino.words())
		self.language = LANGUAGE
		self.lang_id = self.db.languages[LANGUAGE]
		self.vowels = [ "a", "e", "i", "u", "o" ]
		self.double_chars = [ "oe", "ou", "au", "ij", "ui", "ie", "ei", "eu", "oi", "ai" ]


	def adjectiveAntonyms(self):
		print("first redesign")
		exit()
		""" Based on word characteristics. Trying to prefix 'on' to a word. """
		pos_id = self.db.posses["adjective"]
		lexicalEntryIDs = {}
		
		for lexicalEntryIdentifier in self.g.subjects(LEXINFO.partOfSpeech,LEXINFO.adjective):
			label = self.getLabel(lexicalEntryIdentifier)
			if label[:2] != "on":
				lexicalEntryIDs[lexicalEntryIdentifier] = label
	
		for lexicalEntryIdentifier in lexicalEntryIDs:
			source_value = lexicalEntryIDs[lexicalEntryIdentifier]
			guess_antonym = "on" + source_value

			if self.userCheck("tegenstelling", source_value, guess_antonym):
				sensecount = self.countLexicalenses(lexicalEntryIdentifier)
				if sensecount > 1:
					print("multiple senses detected, store manually")
					continue
				elif sensecount == 1:
					# check antonym
					lexicalSenseIdentifier = self.g.value(URIRef(lexicalEntryIdentifier),ONTOLEX.sense,None)
					if (URIRef(lexicalSenseIdentifier),LEXINFO.antonym,None) in self.g:
						print("antonym already detected, moving on")
						continue
				
				# at this point sensecount is 0, or it is safe to move on
				# we might want to store now, first the guess antonym lexicalEntry, then the sense
				self.db.storeCanonical(guess_antonym,self.lang_id,pos_id)
				self.db.addSense(source_value,pos_id,"lexinfo","antonym",guess_antonym,pos_id)


	def adjectiveMaterialNouns(self):
		print("first redesign")
		exit()
		""" Get all material nouns, based on being part of material category."""
		materialSenseIDs = self.getLexicalSenseIDsByReference(["http://www.wikidata.org/entity/Q11344"])
		source_pos_id = self.db.posses["noun"]
		target_pos_id = self.db.posses["adjective"]

		# now get all specific values in lexicalEntries
		for mID in materialSenseIDs:
			for senseID in self.g.objects(URIRef(mID),SKOSTHES.narrowerInstantial):
				lexicalEntryID = str(self.g.value(None,ONTOLEX.sense,URIRef(senseID)))
				self.lexicalEntries[lexicalEntryID] = self.getLabel(senseID)

		for lexicalEntryID in self.lexicalEntries:
			label = self.lexicalEntries[lexicalEntryID]
			guess_adjective = self.__getNounStem(label) + "en"

			if guess_adjective in self.worddb:
				if self.userCheck("bijvoegelijk naamwoord", label, guess_adjective):
					self.db.storeCanonical(guess_adjective,self.lang_id,target_pos_id)
					self.db.addSense(label,source_pos_id,"skos","related",guess_adjective,target_pos_id)


	def formSyllableCounts(self):
		""" Provide a syllable count for all forms. """
		result = self.g.query( """SELECT ?lexicalFormID ?formLabel WHERE {
			?lexicalFormID rdf:type ontolex:Form ;
				ontolex:writtenRep ?formLabel .
			OPTIONAL { ?lexicalFormID isocat:DC-499 ?syllableCount }
			FILTER(!bound(?syllableCount)) }""")

		for row in result:
			lexicalFormID = str(row[0])
			label = str(row[1])
			syllableCount = self.__getSyllableCount(label)
			if self.userCheck("lettergrepen", label, str(syllableCount)):
				form_id = self.db.getID(lexicalFormID,"lexicalForm")
				self.db.updateSyllableCount(form_id,syllableCount,self.lang_id)


	def verbRelatedNouns(self):
		print("first redesign")
		exit()
		""" example. delen -> deling """
		source_pos_id = self.db.posses["verb"]
		target_pos_id = self.db.posses["noun"]

		for lexicalEntryID in self.g.subjects(LEXINFO.partOfSpeech,LEXINFO.verb):
			self.lexicalEntries[lexicalEntryID] = self.getLabel(lexicalEntryID)

		for lexicalEntryID in self.lexicalEntries:
			source_value = self.lexicalEntries[lexicalEntryID]
			guess_noun = source_value[:-2] + "ing"

			if guess_noun in self.worddb and self.userCheck("gerelateerd", source_value, guess_noun):
				if not self.checkLexicalEntryExists(guess_noun,LEXINFO.noun):
					# target entry does not exist, add target and add relation
					self.db.storeCanonical(guess_noun,self.lang_id,target_pos_id)
					targetSenseCount = 0
				else:
					targetLexicalEntryID = self.findLexicalEntry(guess_noun,LEXINFO.noun)
					targetSenseCount = self.countLexicalenses(targetLexicalEntryID)
				
				# this is horrific otherwise to check, think of something better later
				sensecount = self.countLexicalenses(lexicalEntryID)
				if sensecount == 0 and targetSenseCount == 0:
					self.db.addSense(source_value,source_pos_id,"skos","related",guess_noun,target_pos_id)
				else:
					print("either source or target has a sense, not storing relation")


	def verbStems(self):
		for lexicalEntryID in self.g.subjects(LEXINFO.partOfSpeech,LEXINFO.verb):
			use = True
			for lexicalFormID in self.g.objects(URIRef(lexicalEntryID),ONTOLEX.lexicalForm):
				if (URIRef(lexicalFormID),LEXINFO.number,LEXINFO.singular) in self.g and (URIRef(lexicalFormID),LEXINFO.tense,LEXINFO.present) in self.g and (URIRef(lexicalFormID),LEXINFO.person,LEXINFO.firstPerson) in self.g:
					use = False
			if use:
				self.lexicalEntries[str(lexicalEntryID)] = self.getLabel(lexicalEntryID)

		for lexicalEntryID in self.lexicalEntries:
			label = self.lexicalEntries[lexicalEntryID]
			base = label[:-2]
			guess_stem = ""

			# roeien, hooien and bijten, roepen
			if base[-2:] in self.double_chars or base[-3:-1] in self.double_chars:
				guess_stem = base

			# beschermen, zetten
			elif not base[-2:-1] in self.vowels and not base[-1:] in self.vowels:
				if base[-2:-1] == base[-1:]:
					guess_stem = base[:-1]
				else:
					guess_stem = base

			# hanteren, benaderen, keren, handelen, uitwisselen, delen, nemen, ademen
			elif base[-2:] in ["er","em","el","en"]:
				# no apparant rule, so check by random choice
				choice = randint(1,10)
				if choice > 6:
					guess_stem = base
				else:
					guess_stem = base[:-1] + base[-2:-1] + base[-1:]

			# horen, vermenigvuldigen
			elif base[-2:-1] in self.vowels and not base[-1:] in self.vowels:
				if base[-2:-1] in ["a","o","e"]:
					guess_stem = base[:-1] + base[-2:-1] + base[-1:]
				else:
					guess_stem = base

			else:
				print("don't know: " + label)
				continue

			if guess_stem[-1:] == "v":
				guess_stem = guess_stem[:-1] + "f"
			elif guess_stem[-1:] == "z":
				guess_stem = guess_stem[:-1] + "s"

			if guess_stem in self.worddb:
				if self.userCheck("stam", label, "ik " + guess_stem):
					lex_id = self.db.getID(lexicalEntryID,"lexicalEntry")
					form_id = self.db.storeOtherForm(lex_id,guess_stem,self.lang_id)
					self.db.insertFormProperty(form_id,self.db.morphosyntactics["number:singular"],True)
					self.db.insertFormProperty(form_id,self.db.morphosyntactics["tense:present"],True)
					self.db.insertFormProperty(form_id,self.db.morphosyntactics["person:firstPerson"],True)


	def nounPlurals(self):
		# Finding plurals for nouns without a plural form. """
		self.setProcessableEntries(LEXINFO.noun,LEXINFO.number,LEXINFO.plural)
		source_pos_id = self.db.posses["noun"]
		target_pos_id = self.db.posses["noun"]

		for lexicalEntryID in self.lexicalEntries:
			label = self.lexicalEntries[lexicalEntryID]

			if label[-2:] in ["er","ie","en"]:
				guess_plural = label + "s"
			elif label[-2:-1] in self.vowels and not label[-3:-2] in self.vowels:
				guess_plural = label + label[-1:] + "en"
			elif label[-3:] in ["eum","ium"]:
				guess_plural = label[:-2] + "a"
			else:
				guess_plural = self.__getNounStem(label) + "en"

			if guess_plural in self.worddb:
				if self.userCheck("meervoud", label, guess_plural):
					# first get the database identifier and store the plural
					lex_id = self.db.getID(str(lexicalEntryID),"lexicalEntry")
					form_id = self.db.storeOtherForm(lex_id,guess_plural,self.lang_id)
					self.db.insertFormProperty(form_id,self.db.morphosyntactics["number:plural"],True)
					
					# then do the same for the canonicalForm, and store the singular
					lexicalFormID = self.g.value(URIRef(lexicalEntryID),ONTOLEX.canonicalForm,None)
					canonical_form_id = self.db.getID(str(lexicalFormID),"lexicalForm")
					self.db.insertFormProperty(canonical_form_id,self.db.morphosyntactics["number:singular"],True)


	def nounGender(self):
		""" Using rules from http://www.inventio.nl/genus/uitleg.html to detect word gender. """
		# Finding gender for noun forms without a gender.
		self.setProcessableForms(LEXINFO.noun,LEXINFO.gender)

		for lexicalFormID in self.lexicalForms:
			label = self.lexicalForms[lexicalFormID]["label"]
			lexicalEntryID = self.lexicalForms[lexicalFormID]["lexicalEntryID"]
			guess_gender = ""

			# later look if we can make a function for these lookups
			if label[-3:] == "ing" and self.checkLexicalEntryExists(label[:-3] + "en",LEXINFO.verb):
				guess_gender = "feminine"
			elif label[-3:] in ["pje","tje"] or label[-4:] in ["tuig","isme","ment"]:
				guess_gender = "neuter"
			elif len(label) > 5 and label[-4:] in [ "heid", "teit", "tuur", "suur" ]:
				guess_gender = "feminine"
			elif len(label) > 6 and (label[-3:] in ["aar","erd"] or label[-4:] == "aard"):
				guess_gender = "masculine"

			if self.userCheck("geslacht",label,guess_gender):
				form_id = self.db.getID(str(lexicalFormID),"lexicalForm")
				self.db.insertFormProperty(form_id,self.db.morphosyntactics["gender:" + guess_gender],True)


	def nounGenderCategory(self):
		""" Add noun gender neuter based on category. """
		# landen, windstreken, metalen
		self.setProcessableForms(LEXINFO.noun,LEXINFO.gender)
		self.setQuery("getNarrowerInstantialByReference")
		referenceEntryIDs = []

		for ref in ["http://www.wikidata.org/entity/Q6256","http://www.wikidata.org/entity/Q23718","http://www.wikidata.org/entity/Q11426"]:
			for row in self.g.query( self.q_getNarrowerInstantialByReference, initBindings={"reference": URIRef(ref)}):
				referenceEntryIDs.append(str(row[0]))
		
		for lexicalFormID in self.lexicalForms:
			label =  self.lexicalForms[lexicalFormID]["label"]
			lexicalEntryID = self.lexicalForms[lexicalFormID]["lexicalEntryID"]
			
			if lexicalEntryID in referenceEntryIDs:
				if self.userCheck("geslacht", label, "neuter"):
					form_id = self.db.getID(str(lexicalFormID),"lexicalForm")
					self.db.insertFormProperty(form_id,self.db.morphosyntactics["gender:neuter"],True)


	def nounComponentsFind(self):
		pos_id = self.db.posses["noun"]
		components = self.getTopUsedComponents()
		for componentID in components:
			label = self.getLabel(componentID)
			label_len = len(label)
			
			for word in self.worddb:
				if len(word) > label_len and word[-label_len:] == label and not word[0].isupper() and not self.checkLexicalEntryExists(word,LEXINFO.noun):
					if self.userCheck("add as noun", label, word):
						self.db.storeCanonical(word,self.lang_id,pos_id)


	def __getNounStem(self,word):
		""" For example, boom -> bom -> bom + en = bomen."""
		if word[-3:-1] in [ "aa", "ee", "oo" ]:
			  return word[:-3] + word[-3:-2] + word[-1]
		else:
			return word


	def __getSyllableCount(self,word):
		""" records changes to a vowel """
		# still have to work on: gourmette, mythe, recyclen, kampioen, roeien, fluor, opruien, praseodymium, Eritrea, biologie, sensationeel
		# keep checking and finding rules
		vowel = 0
		syllableCount = 0
		previous_char = ""

		for c in word.lower():
			if c in self.vowels:
				if vowel == 0:
					syllableCount += 1
					vowel = 1
				# uranium
				elif c == "u" and previous_char == "i":
					syllableCount += 1
				# neon
				elif c == "o" and previous_char == "e":
					syllableCount += 1
			elif c == "ë":
				syllableCount += 1
			else: 
				vowel = 0 

			previous_char = c

		return syllableCount
