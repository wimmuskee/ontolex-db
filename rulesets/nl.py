# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import SKOS, RDFS, RDF, XSD
from rdflib import Graph
from database.mysql import Database
from nltk.corpus import alpino

ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
LEXINFO = Namespace("http://www.lexinfo.net/ontology/2.0/lexinfo#")
LIME = Namespace("http://www.w3.org/ns/lemon/lime#")
SKOSTHES = Namespace("http://purl.org/iso25964/skos-thes#")
LANGUAGE = "nl"

# always ask first, then check if the thing can be stored, if problem, we can do something later
# also later, we can do more checks, for instance, not checking for possibilities that already exists
#  or checking for words in actual corpora


class Ruleset:
	def __init__(self,config):
		global ONTOLEX
		global LEXINFO
		global LIME
		global SKOSTHES
		global LANGUAGE

		self.db = Database(config)
		self.db.connect()
		self.db.setPosses()
		self.db.setLanguages()

		self.g = Graph()
		self.g.parse("export.ttl", format="turtle")
		# later, check if language is correct
		# lexicon definition with lime language
		# later also check on first lexical entry rdfs language

		# for now use alpino, we should be able to configure this
		self.worddb = alpino.words()


	def adjectiveAntonyms(self):
		""" Based on word characteristics. Trying to prefix 'on' to a word. """
		lang_id = self.db.languages[LANGUAGE]
		pos_id = self.db.posses["adjective"]
		lexicalEntryIDs = {}
		
		for lexicalEntryIdentifier in self.g.subjects(LEXINFO.partOfSpeech,LEXINFO.adjective):
			label = str(self.g.value(URIRef(lexicalEntryIdentifier),RDFS.label,None))
			if label[:2] != "on":
				lexicalEntryIDs[lexicalEntryIdentifier] = label
	
		for lexicalEntryIdentifier in lexicalEntryIDs:
			source_value = lexicalEntryIDs[lexicalEntryIdentifier]
			guess_antonym = "on" + source_value
			
			answer = input("tegenstelling? " + source_value + " :: " + guess_antonym + " ")
			if answer == "y":
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
				self.db.storeCanonical(guess_antonym,lang_id,pos_id)
				self.db.addSense(source_value,pos_id,"lexinfo","antonym",guess_antonym,pos_id)


	def verbRelatedNouns(self):
		""" example. delen -> deling """
		lang_id = self.db.languages[LANGUAGE]
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
				answer = input("gerelateerd? " + source_value + " :: " + guess_noun + " ")
				if answer == "y":
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
					self.db.storeCanonical(guess_noun,lang_id,target_pos_id)
					self.db.addSense(source_value,source_pos_id,"skos","related",guess_noun,target_pos_id)


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