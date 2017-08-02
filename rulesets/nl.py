# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal, Namespace
from rulesets.ruleset import RulesetCommon
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

		if config["worddb"]["type"] == "file":
			self.setWordDbFile(config["worddb"]["name"])
		else:
			from nltk.corpus import alpino
			self.worddb = set(alpino.words())

		self.language = LANGUAGE
		self.lang_id = self.db.languages[LANGUAGE]
		self.vowels = [ "a", "e", "i", "u", "o" ]
		self.double_chars = [ "oe", "ou", "au", "ij", "ui", "ie", "ei", "eu", "oi", "ai" ]


	def adjectiveAntonyms(self):
		# 1. gather adjective lexicalEntries
		self.setLexicalEntriesByPOS(LEXINFO.adjective,["label","senses"])

		# 2. delete entries which have an antonym sense relation, or start with stringmatchers
		for lexicalEntryID in list(self.lexicalEntries):
			meta = self.lexicalEntries[lexicalEntryID]
			if meta["label"][:2] == "on" or meta["label"][:2] == "in":
				del(self.lexicalEntries[lexicalEntryID])
				continue

			for lexicalSenseID in meta["senses"]:
				senseID = self.g.value(URIRef(lexicalSenseID),LEXINFO.antonym,None)
				if senseID:
					del(self.lexicalEntries[lexicalEntryID])
					break

		# 3. apply rulesets to find matches and delete the rest
		for lexicalEntryID in list(self.lexicalEntries):
			label = self.lexicalEntries[lexicalEntryID]["label"]
			self.lexicalEntries[lexicalEntryID]["match"] = {}

			search_antonym = []
			search_antonym.append("in" + label)
			search_antonym.append("on" + label)
			
			for antonym in search_antonym:
				targetLexicalEntryID = self.findLexicalEntry(antonym,LEXINFO.adjective)
				if targetLexicalEntryID:
					self.lexicalEntries[lexicalEntryID]["match"] = {"lexicalEntryID": targetLexicalEntryID, "label": antonym, "senses": self.getLexicalSenseIDs(targetLexicalEntryID)}
					break

			if not self.lexicalEntries[lexicalEntryID]["match"]:
				del(self.lexicalEntries[lexicalEntryID])

		# 4. parse remaining entries with matches, and store
		for lexicalEntryID,meta in self.lexicalEntries.items():
			if len(meta["senses"]) > 1 or len(meta["match"]["senses"]) > 1:
				print("sensecount > 1 for source or target: " + meta["label"])
				continue
			
			if self.userCheck("antonym", meta["label"], meta["match"]["label"]):
				if len(meta["senses"]) == 1:
					source_sense_id = self.db.getID(meta["senses"][0],"lexicalSense")
				else:
					source_entry_id = self.db.getID(lexicalEntryID,"lexicalEntry")
					source_sense_id = self.db.insertLexicalSense(source_entry_id,True)

				if len(meta["match"]["senses"]) == 1:
					target_sense_identifier = meta["match"]["senses"][0]
				else:
					target_entry_id = self.db.getID(meta["match"]["lexicalEntryID"],"lexicalEntry")
					target_sense_id = self.db.insertLexicalSense(target_entry_id,True)
					target_sense_identifier = self.db.getIdentifier(target_sense_id,"lexicalSense")

				self.db.insertSenseReference(source_sense_id,"lexinfo:antonym",target_sense_identifier,True)


	def adjectivePertainsTo(self):
		# 1. gather adjective lexicalEntries
		self.setLexicalEntriesByPOS(LEXINFO.adjective,["label","senses"])

		# 2. delete entries which have a pertainsTo sense relation
		for lexicalEntryID in list(self.lexicalEntries):
			meta = self.lexicalEntries[lexicalEntryID]
			for lexicalSenseID in meta["senses"]:
				senseID = self.g.value(URIRef(lexicalSenseID),LEXINFO.pertainsTo,None)
				if senseID:
					del(self.lexicalEntries[lexicalEntryID])
					break

		# 3. apply rulesets to find matches and delete the rest
		for lexicalEntryID in list(self.lexicalEntries):
			label = self.lexicalEntries[lexicalEntryID]["label"]
			self.lexicalEntries[lexicalEntryID]["match"] = {}

			search_noun = []
			if label[-5:] == "tisch":
				# communistisch -> communisme
				search_noun.append(label[:-5] + "me")
			elif label[-4:] == "isch":
				# chemisch -> chemie
				search_noun.append(label[:-3] + "e")
				# feministisch -> feminisme
				search_noun.append(label[:-3] + "sme")
				# kritisch -> kritiek
				search_noun.append(label[:-3] + "ek")
			elif label[-6:] == "kundig":
				# wiskundig -> wiskunde
				search_noun.append(label[:-2] + "e")
			elif label[-5:] == "oneel":
				# traditioneel -> traditie
				search_noun.append(label[:-5] + "e")

			for noun in search_noun:
				targetLexicalEntryID = self.findLexicalEntry(noun,LEXINFO.noun)
				if targetLexicalEntryID:
					self.lexicalEntries[lexicalEntryID]["match"] = {"lexicalEntryID": targetLexicalEntryID, "label": noun, "senses": self.getLexicalSenseIDs(targetLexicalEntryID)}
					break

			if not self.lexicalEntries[lexicalEntryID]["match"]:
				del(self.lexicalEntries[lexicalEntryID])

		# 4. parse remaining entries with matches, and store
		for lexicalEntryID,meta in self.lexicalEntries.items():
			if len(meta["senses"]) > 1 or len(meta["match"]["senses"]) > 1:
				print("sensecount > 1 for source or target: " + meta["label"])
				continue
			
			if self.userCheck("pertainsTo", meta["label"], meta["match"]["label"]):
				if len(meta["senses"]) == 1:
					source_sense_id = self.db.getID(meta["senses"][0],"lexicalSense")
				else:
					source_entry_id = self.db.getID(lexicalEntryID,"lexicalEntry")
					source_sense_id = self.db.insertLexicalSense(source_entry_id,True)

				if len(meta["match"]["senses"]) == 1:
					target_sense_identifier = meta["match"]["senses"][0]
				else:
					target_entry_id = self.db.getID(meta["match"]["lexicalEntryID"],"lexicalEntry")
					target_sense_id = self.db.insertLexicalSense(target_entry_id,True)
					target_sense_identifier = self.db.getIdentifier(target_sense_id,"lexicalSense")

				self.db.insertSenseReference(source_sense_id,"lexinfo:pertainsTo",target_sense_identifier,True)


	def adjectiveConjugated(self):
		formsToConjugate = {}
		for lexicalEntryID in self.g.subjects(LEXINFO.partOfSpeech,LEXINFO.adjective):
			formdict = self.__getAdjectiveForms(str(lexicalEntryID))

			# find out which forms we should conjugate
			if formdict["canonical"] and not formdict["canonical_c"]:
				formsToConjugate[formdict["canonical"]] = {"lexicalEntryID": str(lexicalEntryID), "degree": "canonical"}
			if formdict["comparative"] and not formdict["comparative_c"]:
				formsToConjugate[formdict["comparative"]] = {"lexicalEntryID": str(lexicalEntryID), "degree": "comparative"}
			if formdict["superlative"] and not formdict["superlative_c"]:
				formsToConjugate[formdict["superlative"]] = {"lexicalEntryID": str(lexicalEntryID), "degree": "superlative"}

		for lexicalFormID in formsToConjugate:
			lexicalEntryID = formsToConjugate[lexicalFormID]["lexicalEntryID"]
			degree = formsToConjugate[lexicalFormID]["degree"]
			label = self.getLabel(lexicalFormID)
			syllableCount = self.__getSyllableCount(label)
			
			if label[-2:-1] in self.vowels and not label[-3:-2] in self.vowels and syllableCount == 1:
				guess_adjective = label + label[-1:] + "e"
			elif label[-3:] == "ief":
				guess_adjective = label[:-1] + "ve"
			else:
				guess_adjective = self.__getNounStem(label) + "e"

			if guess_adjective in self.worddb:
				if self.userCheck("vervoeging bijvoegelijk naamwoord: " + degree, label, guess_adjective):
					lex_id = self.db.getID(lexicalEntryID,"lexicalEntry")
					form_id = self.db.storeOtherForm(lex_id,guess_adjective,self.lang_id)
					self.db.insertFormProperty(form_id,self.db.properties["morphosyntacticProperty:DC-2207"],True)
					if degree != "canonical":
						self.db.insertFormProperty(form_id,self.db.properties["degree:" + degree],True)


	def adjectivePresentParticiple(self):
		""" Set adjective as copy from verb present participles """
		self.setQuery("askCanonicalByPOS")

		result = self.g.query("""SELECT ?label ?lexicalEntryID WHERE {
			?lexicalEntryID rdf:type ontolex:LexicalEntry ;
				lexinfo:partOfSpeech lexinfo:verb ;
				ontolex:otherForm ?lexicalFormID .
			?lexicalFormID lexinfo:verbFormMood lexinfo:participle ;
				lexinfo:tense lexinfo:present ;
				rdfs:label ?label . }""")

		for row in result:
			label = str(row[0])
			lexicalEntryID = str(row[1])

			# first check if label already exists as presentParticipleAdjective
			if not bool(self.g.query(self.q_askCanonicalByPOS, initBindings={"label": Literal(label, lang="nl"), "partOfSpeech": LEXINFO.presentParticipleAdjective})):
				# it might exist as a plain adjective
				if bool(self.g.query(self.q_askCanonicalByPOS, initBindings={"label": Literal(label, lang="nl"), "partOfSpeech": LEXINFO.adjective})):
					lex_id = self.db.getLexicalEntryID(label,self.db.posses["adjective"])
					self.db.updateLexicalEntryPOS(lex_id,self.db.posses["presentParticipleAdjective"])
				else:
					lex_id = self.db.storeCanonical(label,self.lang_id,self.db.posses["presentParticipleAdjective"])
					self.db.insertLexicalEntryRelation(lex_id,self.db.entryrelations["lexinfo:participleFormOf"],lexicalEntryID,True)
				self.db.insertLexicalEntryRelation(lex_id,self.db.entryrelations["lexinfo:participleFormOf"],lexicalEntryID,True)


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
				self.lexicalEntries[lexicalEntryID]["label"] = self.getLabel(senseID)

		for lexicalEntryID in self.lexicalEntries:
			label = self.lexicalEntries[lexicalEntryID]["label"]
			guess_adjective = self.__getNounStem(label) + "en"

			if guess_adjective in self.worddb:
				if self.userCheck("bijvoegelijk naamwoord", label, guess_adjective):
					self.db.storeCanonical(guess_adjective,self.lang_id,target_pos_id)
					self.db.addSense(label,source_pos_id,"skos","related",guess_adjective,target_pos_id)


	def formSyllableCounts(self):
		""" Provide a syllable count for all forms. """
		data = self.db.getWrittenRepsWithoutSyllableCount(self.lang_id)
		for row in data:
			label = row["value"]
			syllableCount = self.__getSyllableCount(label)
			if self.userCheck("lettergrepen", label, str(syllableCount)):
				self.db.updateSyllableCount(label,syllableCount,self.lang_id)


	def verbPastParticiples(self):
		# 1. get verbs
		self.setLexicalEntriesByPOS(LEXINFO.verb,["label","forms"])
		self.filterEntriesRemoveComponentBased()

		# 2. keep entries with a past singular but not a past participle
		for lexicalEntryID in list(self.lexicalEntries):
			self.lexicalEntries[lexicalEntryID]["stem"] = ""
			for lexicalFormID in self.lexicalEntries[lexicalEntryID]["forms"]:
				if (URIRef(lexicalFormID),LEXINFO.verbFormMood,LEXINFO.participle) in self.g and (URIRef(lexicalFormID),LEXINFO.tense,LEXINFO.past) in self.g:
					del(self.lexicalEntries[lexicalEntryID])
					break
				if (URIRef(lexicalFormID),LEXINFO.number,LEXINFO.singular) in self.g and (URIRef(lexicalFormID),LEXINFO.tense,LEXINFO.past) in self.g:
					self.lexicalEntries[lexicalEntryID]["stem"] = self.getLabel(lexicalFormID)

			if lexicalEntryID in self.lexicalEntries and not self.lexicalEntries[lexicalEntryID]["stem"]:
				del(self.lexicalEntries[lexicalEntryID])

		# 3. make participle, check and save
		for lexicalEntryID,meta in self.lexicalEntries.items():
			label = meta["stem"]
			original = meta["label"]

			# fix trema start
			if label[0] == "e":
				label = "ë" + label[1:]
			elif label[0] == "i" and label[1] != "j":
				label = "ï" + label[1:]

			prefixes = ["ge","be","ver","ont","her"]

			if (label[:2] in prefixes or label[:3] in prefixes) and (label[-3:] == "dde" or label[-3:] == "tte"):
				# begroette -> begroet, verlootte -> verloot
				guess_participle = label[:-2]
			elif (label[:2] in prefixes or label[:3] in prefixes) and (label[-2:] == "de" or label[-2:] == "te"):
				# verzekerde -> verzekerd, belazerde -> belazerd
				guess_participle = label[:-1]
			elif label[-3:-1] == "dd" or label[-3:-1] == "tt":
				# lootte -> geloot
				guess_participle = "ge" + label[:-2]
			elif label[-1:] == "e":
				# stoorde -> gestoord
				guess_participle = "ge" + label[:-1]
			elif label[:2] in prefixes or label[:3] in prefixes:
				# vergeven -> vergeven (indeed not working for all)
				guess_participle = label
			elif label[-2:-1] not in self.vowels:
				# bond -> gebonden
				guess_participle = "ge" + label + "en"
			else:
				# vloog -> gevlogen
				label = self.__getStemToPluralizeCheck(label)
				guess_participle = "ge" + label[:-2] + label[-1] + "en"

			if self.userCheck("voltooid deelwoord", original, "ik ben/heb " + guess_participle):
				self.db.saveVerbPastParticiple(lexicalEntryID,guess_participle,self.lang_id)
			else:
				answer = input("manual? provide value or press enter to cancel ")
				if len(answer) > 1:
					self.db.saveVerbPastParticiple(lexicalEntryID,answer,self.lang_id)


	def verbPastSingulars(self):
		# 1. get verbs
		self.setLexicalEntriesByPOS(LEXINFO.verb,["label","forms"])

		# 2. keep entries with present singular firstPerson form (and no past singular form
		for lexicalEntryID in list(self.lexicalEntries):
			self.lexicalEntries[lexicalEntryID]["stem"] = ""
			for lexicalFormID in self.lexicalEntries[lexicalEntryID]["forms"]:
				if (URIRef(lexicalFormID),LEXINFO.number,LEXINFO.singular) in self.g and (URIRef(lexicalFormID),LEXINFO.tense,LEXINFO.past) in self.g:
					del(self.lexicalEntries[lexicalEntryID])
					break
				if (URIRef(lexicalFormID),LEXINFO.number,LEXINFO.singular) in self.g and (URIRef(lexicalFormID),LEXINFO.tense,LEXINFO.present) in self.g and (URIRef(lexicalFormID),LEXINFO.person,LEXINFO.firstPerson) in self.g:
					self.lexicalEntries[lexicalEntryID]["stem"] = self.getLabel(lexicalFormID)

			if lexicalEntryID in self.lexicalEntries and not self.lexicalEntries[lexicalEntryID]["stem"]:
				del(self.lexicalEntries[lexicalEntryID])

		# 3. make past form and check
		for lexicalEntryID, meta in self.lexicalEntries.items():
			infinitive_stem_lastchar = meta["label"][-3:-2]

			if infinitive_stem_lastchar in [ "t","k","f","s","c","h","p","x"]:
				guess_past = meta["stem"] + "te"
			else:
				guess_past = meta["stem"] + "de"

			if self.userCheck("verleden tijd ev", meta["label"], "ik/jij/hij " + guess_past):
				self.db.saveVerbPastSingular(lexicalEntryID,guess_past,self.lang_id)
			else:
				answer = input("manual? provide value or press enter to cancel ")
				if len(answer) > 1:
					self.db.saveVerbPastSingular(lexicalEntryID,answer,self.lang_id)


	def verbPastPlurals(self):
		# 1. get verbs
		self.setLexicalEntriesByPOS(LEXINFO.verb,["label","forms"])
		self.filterEntriesRemoveComponentBased()

		# 2. keep entries with a past singular but not a plural
		for lexicalEntryID in list(self.lexicalEntries):
			self.lexicalEntries[lexicalEntryID]["stem"] = ""

			for lexicalFormID in self.lexicalEntries[lexicalEntryID]["forms"]:
				if (URIRef(lexicalFormID),LEXINFO.number,LEXINFO.plural) in self.g and (URIRef(lexicalFormID),LEXINFO.tense,LEXINFO.past) in self.g:
					del(self.lexicalEntries[lexicalEntryID])
					break
				if (URIRef(lexicalFormID),LEXINFO.number,LEXINFO.singular) in self.g and (URIRef(lexicalFormID),LEXINFO.tense,LEXINFO.past) in self.g:
					self.lexicalEntries[lexicalEntryID]["stem"] = self.getLabel(lexicalFormID)

			if lexicalEntryID in self.lexicalEntries and not self.lexicalEntries[lexicalEntryID]["stem"]:
				del(self.lexicalEntries[lexicalEntryID])

		# 3. make past form and check
		for lexicalEntryID, meta in self.lexicalEntries.items():
			label = meta["stem"]

			if label[-2:] == "te" or label[-2:] == "de":
				guess_plural = label + "n"
			elif label[-2:-1] in self.vowels and label[-3:-2] in self.vowels:
				# sleep -> slepen
				label = self.__getStemToPluralizeCheck(label)
				guess_plural = label[:-2] + label[-1:] + "en"
			elif label[-2:-1] in self.vowels and not label[-3:-2] in self.vowels:
				# zwom -> zwommen
				guess_plural = label + label[-1:] + "en"
			else:
				guess_plural = label + "en"

			if self.userCheck("verleden tijd mv", label, "wij " + guess_plural):
				lex_id = self.db.getID(lexicalEntryID,"lexicalEntry")
				# turning off safemode in storeOtherForm, infinitive "bevatten" is also past plural "bevatten"
				form_id = self.db.storeOtherForm(lex_id,guess_plural,self.lang_id,False)
				self.db.insertFormProperty(form_id,self.db.properties["tense:past"],True)
				self.db.insertFormProperty(form_id,self.db.properties["number:plural"],True)


	def verbPresentParticiples(self):
		""" detecting present participles from canonical verbs """
		result = self.g.query("""SELECT ?label ?lexicalEntryID WHERE {
			?lexicalEntryID rdf:type ontolex:LexicalEntry ;
				lexinfo:partOfSpeech lexinfo:verb ;
				rdfs:label ?label .
			MINUS { 
				?lexicalEntryID ontolex:otherForm ?lexicalParticipleID .
				?lexicalParticipleID lexinfo:verbFormMood lexinfo:participle ;
					lexinfo:tense lexinfo:present . } }""")

		for row in result:
			label = str(row[0])
			lexicalEntryID = str(row[1])
			guess_participle = label + "d"

			if guess_participle in self.worddb:
				if self.userCheck("deelwoord tegenwoordige tijd", label, guess_participle):
					lex_id = self.db.getID(lexicalEntryID,"lexicalEntry")
					form_id = self.db.storeOtherForm(lex_id,guess_participle,self.lang_id)
					self.db.insertFormProperty(form_id,self.db.properties["tense:present"],True)
					self.db.insertFormProperty(form_id,self.db.properties["verbFormMood:participle"],True)


	def verbRelatedNouns(self):
		# 1. gather verb lexicalEntries
		self.setLexicalEntriesByPOS(LEXINFO.verb,["label","senses"])

		# 2. delete entries which we don't want to parse
		for lexicalEntryID in list(self.lexicalEntries):
			if self.lexicalEntries[lexicalEntryID]["label"][-2:] != "en":
				del(self.lexicalEntries[lexicalEntryID])
				continue

		# 3.1 add matches
		for lexicalEntryID in list(self.lexicalEntries):
			label = self.lexicalEntries[lexicalEntryID]["label"]
			self.lexicalEntries[lexicalEntryID]["match"] = {}

			search_noun = []
			search_noun.append(label[:-2] + "ing")
			# later, add delen -> deel

			for noun in search_noun:
				targetLexicalEntryID = self.findLexicalEntry(noun,LEXINFO.noun)
				if targetLexicalEntryID:
					self.lexicalEntries[lexicalEntryID]["match"] = {"lexicalEntryID": targetLexicalEntryID, "label": noun, "senses": self.getLexicalSenseIDs(targetLexicalEntryID)}
					

			if not self.lexicalEntries[lexicalEntryID]["match"]:
				del(self.lexicalEntries[lexicalEntryID])

		# 3.2 remove entries for which match exists
		for lexicalEntryID in list(self.lexicalEntries):
			for sourceSenseID in self.lexicalEntries[lexicalEntryID]["senses"]:
				for targetSenseID in self.lexicalEntries[lexicalEntryID]["match"]["senses"]:
					if (URIRef(sourceSenseID),LEXINFO.relatedTerm,URIRef(targetSenseID)) in self.g:
						del(self.lexicalEntries[lexicalEntryID])
						break

		# 4. parse remaining entries with matches, and store
		for lexicalEntryID,meta in self.lexicalEntries.items():
			if len(meta["senses"]) > 1 or len(meta["match"]["senses"]) > 1:
				print("sensecount > 1 for source or target: " + meta["label"])
				continue

			if self.userCheck("relatedTerm", meta["label"], meta["match"]["label"]):
				if len(meta["senses"]) == 1:
					source_sense_id = self.db.getID(meta["senses"][0],"lexicalSense")
				else:
					source_entry_id = self.db.getID(lexicalEntryID,"lexicalEntry")
					source_sense_id = self.db.insertLexicalSense(source_entry_id,True)

				if len(meta["match"]["senses"]) == 1:
					target_sense_identifier = meta["match"]["senses"][0]
				else:
					target_entry_id = self.db.getID(meta["match"]["lexicalEntryID"],"lexicalEntry")
					target_sense_id = self.db.insertLexicalSense(target_entry_id,True)
					target_sense_identifier = self.db.getIdentifier(target_sense_id,"lexicalSense")

				self.db.insertSenseReference(source_sense_id,"lexinfo:relatedTerm",target_sense_identifier,True)


	def verbSingulars(self):
		"""Add remaining singulars to verbs with stems set."""
		for lexicalEntryID in self.g.subjects(LEXINFO.partOfSpeech,LEXINFO.verb):
			use = True
			stem = ""
			form_identifier = ""
			for lexicalFormID in self.g.objects(URIRef(lexicalEntryID),ONTOLEX.otherForm):
				if (URIRef(lexicalFormID),LEXINFO.number,LEXINFO.singular) in self.g and (URIRef(lexicalFormID),LEXINFO.tense,LEXINFO.present) in self.g and (URIRef(lexicalFormID),LEXINFO.person,LEXINFO.firstPerson) in self.g:
					stem = self.getLabel(str(lexicalFormID))
					form_identifier = str(lexicalFormID)
				if (URIRef(lexicalFormID),LEXINFO.number,LEXINFO.singular) in self.g and (URIRef(lexicalFormID),LEXINFO.tense,LEXINFO.present) in self.g and (URIRef(lexicalFormID),LEXINFO.person,LEXINFO.secondPerson) in self.g:
					use = False
			if use:
				self.lexicalForms[form_identifier] = stem

		for lexicalFormID in self.lexicalForms:
			label = self.lexicalForms[lexicalFormID]
			singular_unique = False

			# stoot
			if label[-1:] == "t":
				guess_singular = label
				# no worddb check, but ask to add formprops to form
				if self.userCheck("enkelvoud", "ik " + label, "jij/hij " + guess_singular):
					form_id = self.db.getID(lexicalFormID,"lexicalForm")
					self.db.insertFormProperty(form_id,self.db.properties["person:secondPerson"],True)
					self.db.insertFormProperty(form_id,self.db.properties["person:thirdPerson"],True)
			# ga, onsta
			elif label[-1:] == "a":
				guess_singular = label + "at"
				singular_unique = True
			else:
				guess_singular = label + "t"
				singular_unique = True

			if singular_unique:
				if self.userCheck("enkelvoud", "ik " + label, "jij/hij " + guess_singular):
					lexicalEntryID = self.g.value(None,ONTOLEX.otherForm,URIRef(lexicalFormID))
					lex_id = self.db.getID(lexicalEntryID,"lexicalEntry")
					form_id = self.db.storeOtherForm(lex_id,guess_singular,self.lang_id)
					self.db.insertFormProperty(form_id,self.db.properties["number:singular"],True)
					self.db.insertFormProperty(form_id,self.db.properties["tense:present"],True)
					self.db.insertFormProperty(form_id,self.db.properties["person:secondPerson"],True)
					self.db.insertFormProperty(form_id,self.db.properties["person:thirdPerson"],True)


	def verbStems(self):
		# 1. gather verb lexicalEntries
		self.setLexicalEntriesByPOS(LEXINFO.verb,["label","forms"])
		self.filterEntriesRemoveComponentBased()

		# 2. delete entries which have 
		for lexicalEntryID in list(self.lexicalEntries):
			for lexicalFormID in self.lexicalEntries[lexicalEntryID]["forms"]:
				if (URIRef(lexicalFormID),LEXINFO.number,LEXINFO.singular) in self.g and (URIRef(lexicalFormID),LEXINFO.tense,LEXINFO.present) in self.g and (URIRef(lexicalFormID),LEXINFO.person,LEXINFO.firstPerson) in self.g:
					del(self.lexicalEntries[lexicalEntryID])
					break

		# 3. apply rulesets and store
		for lexicalEntryID in list(self.lexicalEntries):
			label = self.lexicalEntries[lexicalEntryID]["label"]
			base = label[:-2]
			guess_stem = ""

			if base[-2:] in self.double_chars or base[-3:-1] in self.double_chars:
				# roeien, hooien and bijten, roepen
				guess_stem = base
			elif not base[-2:-1] in self.vowels and not base[-1:] in self.vowels:
				# zetten -> beschermen
				if base[-2:-1] == base[-1:]:
					guess_stem = base[:-1]
				else:
					guess_stem = base
			elif base[-2:] in ["er","em","el","en"]:
				# hanteren, benaderen, keren, handelen, uitwisselen, delen, nemen, ademen
				# no apparant rule, so check by random choice
				choice = randint(1,10)
				if choice > 6:
					guess_stem = base
				else:
					guess_stem = base[:-1] + base[-2:-1] + base[-1:]
			elif base[-2:-1] in self.vowels and not base[-1:] in self.vowels:
				# horen, vermenigvuldigen, gluren
				if base[-2:-1] in ["a","o","e","u"]:
					# make longer
					guess_stem = base[:-1] + base[-2:-1] + base[-1:]
				else:
					guess_stem = base
			elif label[-3:] == "aan":
				# gaan, ontstaan
				guess_stem = label[:-2]

			if guess_stem[-1:] == "v":
				guess_stem = guess_stem[:-1] + "f"
			elif guess_stem[-1:] == "z":
				guess_stem = guess_stem[:-1] + "s"

			if self.userCheck("stam", label, "ik " + guess_stem):
				lex_id = self.db.getID(lexicalEntryID,"lexicalEntry")
				form_id = self.db.storeOtherForm(lex_id,guess_stem,self.lang_id)
				self.db.insertFormProperty(form_id,self.db.properties["number:singular"],True)
				self.db.insertFormProperty(form_id,self.db.properties["tense:present"],True)
				self.db.insertFormProperty(form_id,self.db.properties["person:firstPerson"],True)


	def nounPlurals(self):
		# looking for plurals, but only for those entries that have no canonical number property
		result = self.g.query("""SELECT ?label ?lexicalEntryID WHERE {
			?lexicalEntryID rdf:type ontolex:LexicalEntry ;
				lexinfo:partOfSpeech lexinfo:noun ;
				rdfs:label ?label .
			MINUS { 
				?lexicalEntryID ontolex:canonicalForm ?lexicalFormID .
				?lexicalFormID lexinfo:number ?number . } }""")

		for row in result:
			label = str(row[0])
			lexicalEntryID = str(row[1])
			syllableCount = self.__getSyllableCount(label)

			if (label[-2:] in ["er","ie","en","el"] or label[-1:] == "e") and syllableCount > 1:
				guess_plural = label + "s"
			elif label[-4:] == "erik":
				guess_plural = label + "en"
			elif label[-2:] == "ij":
				guess_plural = label + "en"
			elif label[-2:-1] in self.vowels and not label[-3:-2] in self.vowels:
				guess_plural = label + label[-1:] + "en"
			elif label[-3:] in ["eum","ium"]:
				guess_plural = label[:-2] + "a"
			elif label[-1:] in ["a","o"]:
				guess_plural = label + "'s"
			elif label[-1:] == "e" and syllableCount == 1:
				guess_plural = label + "ën"
			elif label[-4:] == "heid":
				guess_plural = label[:-2] + "den"
			else:
				label = self.__getStemToPluralizeCheck(label)
				guess_plural = self.__getNounStem(label) + "en"

			if guess_plural in self.worddb:
				if self.userCheck("meervoud", label, guess_plural):
					# first get the database identifier and store the plural
					lex_id = self.db.getID(str(lexicalEntryID),"lexicalEntry")
					form_id = self.db.storeOtherForm(lex_id,guess_plural,self.lang_id)
					self.db.insertFormProperty(form_id,self.db.properties["number:plural"],True)
					
					# then do the same for the canonicalForm, and store the singular
					lexicalFormID = self.g.value(URIRef(lexicalEntryID),ONTOLEX.canonicalForm,None)
					canonical_form_id = self.db.getID(str(lexicalFormID),"lexicalForm")
					self.db.insertFormProperty(canonical_form_id,self.db.properties["number:singular"],True)


	def nounDiminutives(self):
		self.setLexicalEntriesByPOS(LEXINFO.noun,["label","forms"])

		for lexicalEntryID in list(self.lexicalEntries):
			for lexicalFormID in self.lexicalEntries[lexicalEntryID]["forms"]:
				if (URIRef(lexicalFormID),LEXINFO.partOfSpeech,LEXINFO.diminutiveNoun) in self.g:
					del(self.lexicalEntries[lexicalEntryID])
					break

		for lexicalEntryID in self.lexicalEntries:
			label = self.lexicalEntries[lexicalEntryID]["label"]
			syllableCount = self.__getSyllableCount(label)
			guess_diminutive = ""
			
			# zon
			if syllableCount == 1 and not label[-3:-2] in self.vowels and label[-2:-1] in self.vowels:
				guess_diminutive = label + label[-1:] + "etje"
			# boom
			elif label[-1:] == "m":
				guess_diminutive = label + "pje"
			elif label[-1:] in self.vowels:
				guess_diminutive = label + "tje"
			else:
				guess_diminutive = label + "je"

			if guess_diminutive in self.worddb:
				if self.userCheck("verkleining",label,guess_diminutive):
					lex_id = self.db.getID(str(lexicalEntryID),"lexicalEntry")
					# store singular
					singular_form_id = self.db.storeOtherForm(lex_id,guess_diminutive,self.lang_id)
					self.db.insertFormProperty(singular_form_id,self.db.properties["number:singular"],True)
					self.db.insertFormProperty(singular_form_id,self.db.properties["partOfSpeech:diminutiveNoun"],True)
					self.db.insertFormProperty(singular_form_id,self.db.properties["gender:neuter"],True)
					# and plural
					guess_diminutive = guess_diminutive + "s"
					plural_form_id = self.db.storeOtherForm(lex_id,guess_diminutive,self.lang_id)
					self.db.insertFormProperty(plural_form_id,self.db.properties["number:plural"],True)
					self.db.insertFormProperty(plural_form_id,self.db.properties["partOfSpeech:diminutiveNoun"],True)


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
				self.db.insertFormProperty(form_id,self.db.properties["gender:" + guess_gender],True)


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
					self.db.insertFormProperty(form_id,self.db.properties["gender:neuter"],True)


	def nounComponentsFind(self):
		print("first redesign")
		exit()
		pos_id = self.db.posses["noun"]
		components = self.getTopUsedComponents()
		for componentID in components:
			label = self.getLabel(componentID)
			label_len = len(label)
			
			for word in self.worddb:
				if len(word) > label_len and word[-label_len:] == label and not word[0].isupper() and not self.checkLexicalEntryExists(word,LEXINFO.noun):
					if self.userCheck("add as noun", label, word):
						self.db.storeCanonical(word,self.lang_id,pos_id)


	def __getStemToPluralizeCheck(self,stem):
		""" Makes sure stem ending in f or s can be pluralized with correct endings. """
		if stem[-1:] == "f":
			stem = stem[:-1] + "v"
		elif stem[-1:] == "s":
			stem = stem[:-1] + "z"
		return stem


	def __getNounStem(self,word):
		""" For example, boom -> bom -> bom + en = bomen."""
		if word[-3:-1] in [ "aa", "ee", "oo", "uu" ]:
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


	def __getAdjectiveForms(self,lexicalEntryID):
		""" Return the different forms if any for an adjective lexical entry."""
		formdict = { "canonical": "", "canonical_c": "", "comparative": "", "comparative_c": "", "superlative": "", "superlative_c": "" }
		formdict["canonical"] = str(self.g.value(URIRef(lexicalEntryID),ONTOLEX.canonicalForm,None))

		for lexicalFormID in self.g.objects(URIRef(lexicalEntryID),ONTOLEX.otherForm):
			if (URIRef(lexicalFormID),LEXINFO.morphosyntacticProperty,URIRef(ISOCAT + "DC-2207")) in self.g and not (URIRef(lexicalFormID),LEXINFO.degree,LEXINFO.comparative) in self.g and not (URIRef(lexicalFormID),LEXINFO.degree,LEXINFO.superlative) in self.g:
				formdict["canonical_c"] = str(lexicalFormID)
			elif (URIRef(lexicalFormID),LEXINFO.degree,LEXINFO.comparative) in self.g and not (URIRef(lexicalFormID),LEXINFO.morphosyntacticProperty,URIRef(ISOCAT + "DC-2207")) in self.g:
				formdict["comparative"] = str(lexicalFormID)
			elif (URIRef(lexicalFormID),LEXINFO.degree,LEXINFO.comparative) in self.g and (URIRef(lexicalFormID),LEXINFO.morphosyntacticProperty,URIRef(ISOCAT + "DC-2207")) in self.g:
				formdict["comparative_c"] = str(lexicalFormID)
			elif (URIRef(lexicalFormID),LEXINFO.degree,LEXINFO.superlative) in self.g and not (URIRef(lexicalFormID),LEXINFO.morphosyntacticProperty,URIRef(ISOCAT + "DC-2207")) in self.g:
				formdict["superlative"] = str(lexicalFormID)
			elif (URIRef(lexicalFormID),LEXINFO.degree,LEXINFO.superlative) in self.g and (URIRef(lexicalFormID),LEXINFO.morphosyntacticProperty,URIRef(ISOCAT + "DC-2207")) in self.g:
				formdict["superlative_c"] = str(lexicalFormID)

		return formdict
