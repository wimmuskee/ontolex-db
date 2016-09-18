# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import SKOS, RDFS, RDF, XSD
from rulesets.ruleset import RulesetCommon
from nltk.corpus import alpino

ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
LEXINFO = Namespace("http://www.lexinfo.net/ontology/2.0/lexinfo#")
SKOSTHES = Namespace("http://purl.org/iso25964/skos-thes#")
LANGUAGE = "nl"


class Ruleset(RulesetCommon):
	def __init__(self,config):
		RulesetCommon.__init__(self,config)
		global ONTOLEX
		global LEXINFO
		global SKOSTHES
		global LANGUAGE

		# for now use alpino, we should be able to configure this
		self.worddb = alpino.words()
		self.lang_id = self.db.languages[LANGUAGE]


	def adjectiveAntonyms(self):
		""" Based on word characteristics. Trying to prefix 'on' to a word. """
		pos_id = self.db.posses["adjective"]
		lexicalEntryIDs = {}
		
		for lexicalEntryIdentifier in self.g.subjects(LEXINFO.partOfSpeech,LEXINFO.adjective):
			label = str(self.g.value(URIRef(lexicalEntryIdentifier),RDFS.label,None))
			if label[:2] != "on":
				lexicalEntryIDs[lexicalEntryIdentifier] = label
	
		for lexicalEntryIdentifier in lexicalEntryIDs:
			source_value = lexicalEntryIDs[lexicalEntryIdentifier]
			guess_antonym = "on" + source_value

			if self.userCheck("tegenstelling", source_value, guess_antonym):
				sensecount = self.__countLexicalenses(lexicalEntryIdentifier)
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


	def verbRelatedNouns(self):
		""" example. delen -> deling """
		source_pos_id = self.db.posses["verb"]
		target_pos_id = self.db.posses["noun"]
		lexicalEntryIDs = {}

		for lexicalEntryIdentifier in self.g.subjects(LEXINFO.partOfSpeech,LEXINFO.verb):
			label = str(self.g.value(URIRef(lexicalEntryIdentifier),RDFS.label,None))
			lexicalEntryIDs[lexicalEntryIdentifier] = label

		for lexicalEntryIdentifier in lexicalEntryIDs:
			source_value = lexicalEntryIDs[lexicalEntryIdentifier]
			guess_noun = source_value[:-2] + "ing"

			# also, perhaps make this configurable as well
			if guess_noun in self.worddb:
				if self.userCheck("gerelateerd", source_value, guess_noun):
					sensecount = self.__countLexicalenses(lexicalEntryIdentifier)
					if sensecount > 1:
						print("multiple senses detected, store manually")
						continue
					elif sensecount == 1:
						# check if relation to term exists
						if self.__checkLexicalEntryExists(guess_noun, LEXINFO.noun):
							# bit lazy here, but just playing now
							print("entry found for target, so maybe it is connected already")
							continue
					
					# at this point sensecount is 0, or it is safe to move on
					self.db.storeCanonical(guess_noun,self.lang_id,target_pos_id)
					self.db.addSense(source_value,source_pos_id,"skos","related",guess_noun,target_pos_id)


	def nounPlurals(self):
		source_pos_id = self.db.posses["noun"]
		target_pos_id = self.db.posses["noun"]
		lexicalEntryIDs = {}
		
		# first find the entries without a plural
		for lexicalEntryID in self.g.subjects(LEXINFO.partOfSpeech,LEXINFO.noun):
			if self.__checkFormRelation(lexicalEntryID,LEXINFO.number,LEXINFO.plural):
				continue
			lexicalEntryIDs[lexicalEntryID] = str(self.g.value(URIRef(lexicalEntryID),RDFS.label,None))

		for lexicalEntryID in lexicalEntryIDs:
			label = lexicalEntryIDs[lexicalEntryID]
			guess_plural = self.__getNounStemToPlural(label) + "en"

			if guess_plural in self.worddb:
				if self.userCheck("meervoud", label, guess_plural):
					# first get the database identifier and store the plural
					lex_id = self.db.getLexicalEntryIDByIdentifier(str(lexicalEntryID))
					self.db.storeOtherForm(lex_id,guess_plural,self.lang_id,["number:plural"])
					
					# then do the same for the canonicalForm, and store the singular
					lexicalFormID = self.g.value(URIRef(lexicalEntryID),ONTOLEX.canonicalForm,None)
					form_id = self.db.getLexicalFormID(str(lexicalFormID))
					self.db.storeFormProperty(form_id,self.db.morphosyntactics["number:singular"])
					self.db.DB.commit()


	def nounGender(self):
		""" Using rules from http://www.inventio.nl/genus/uitleg.html to detect word gender. """
		# Finding gender for noun forms without a gender.
		self.setProcessableForms(LEXINFO.noun,LEXINFO.gender)
		geoSenseIDs = self.getLexicalSenseIDsByReference(["http://www.wikidata.org/entity/Q6256"])
		
		for lexicalFormID in self.lexicalForms:
			label = self.lexicalForms[lexicalFormID]["label"]
			lexicalEntryID = self.lexicalForms[lexicalFormID]["lexicalEntryID"]
			guess_gender = ""

			# we want to check all forms, unless the sense gives us other info (only in the case of countries and placenames)
			# when first char is uppercase, we're gonna assume sense lookup first
			if label[0].isupper():
				guess_gender = self.__getNounGenderBySense(lexicalEntryID,geoSenseIDs)
			else:
				# find by label rules
				pass
			
			if self.userCheck("geslacht",label,guess_gender):
				form_id = self.db.getLexicalFormID(str(lexicalFormID))
				self.db.storeFormProperty(form_id,self.db.morphosyntactics["gender:" + guess_gender])
				self.db.DB.commit()


	def __getNounGenderBySense(self,lexicalEntryID,geoSenseIDs):
		for geoSenseID in geoSenseIDs:
			if self.__checkSenseRelation(URIRef(lexicalEntryID),SKOSTHES.broaderInstantial,URIRef(geoSenseID)):
				return "neuter"
		return ""


	def __countLexicalenses(self,lexicalEntryIdentifier):
		c = 0
		for lexicalSenseIdentifier in self.g.objects(URIRef(lexicalEntryIdentifier),ONTOLEX.sense):
			c = c + 1
		return c


	def __checkLexicalEntryExists(self,word,partOfSpeech):
		for lexicalEntryIdentifier in self.g.subjects(LEXINFO.partOfSpeech,partOfSpeech):
			if (URIRef(lexicalEntryIdentifier),RDFS.label,Literal(word, lang=LANGUAGE)) in self.g:
				return True
		return False


	def __checkFormRelation(self,lexicalEntryID,checkPredicate,checkObject):
		""" Given a lexicalEntryID, check all related forms to see if the requested relation is present."""
		for lexicalFormID in self.g.objects(URIRef(lexicalEntryID),ONTOLEX.otherForm):
			if (URIRef(lexicalFormID),checkPredicate,checkObject) in self.g:
				return True
		return False


	def __checkSenseRelation(self,lexicalEntryID,checkPredicate,checkObject):
		""" Given a lexicalEntryID, check all related senses to see if the requested relation is present."""
		for lexicalSenseID in self.g.objects(URIRef(lexicalEntryID),ONTOLEX.sense):
			if (URIRef(lexicalSenseID),checkPredicate,checkObject) in self.g:
				return True
		return False


	def __getNounStemToPlural(self,word):
		""" For example, boom -> bom -> bom + en = bomen."""
		if word[-3:-1] in [ "aa", "ee", "oo" ]:
			  return word[-3:-2] + word[-1]
		else:
			return word
