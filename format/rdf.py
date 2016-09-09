# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import SKOS, RDFS, RDF
from rdflib import Graph

ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
LEXINFO = Namespace("http://www.lexinfo.net/ontology/2.0/lexinfo#")

class RDFGraph:
	def __init__(self,format):
		global ONTOLEX
		global LEXINFO

		self.format = format
		self.g = Graph()
		self.g.bind("ontolex", ONTOLEX)
		self.g.bind("lexinfo", LEXINFO)


	def setLexicalEntries(self,lexicalEntries):
		for entry in lexicalEntries:
			lexicalEntryIdentifier = self.__getIdentifier("lex",entry["lex_value"],entry["lexicalEntryID"])

			self.g.add((lexicalEntryIdentifier,RDF.type,ONTOLEX.lexicalEntry))
			self.g.add((lexicalEntryIdentifier,RDF.type,URIRef(ONTOLEX + entry["class"])))
			self.g.add((lexicalEntryIdentifier,LEXINFO.partOfSpeech,URIRef(LEXINFO + entry["pos_value"])))


	def setLexicalForms(self,lexicalForms):
		for form in lexicalForms:
			lexicalEntryIdentifier = self.__getIdentifier("lex",form["lex_value"],form["lexicalEntryID"])
			lexicalFormIdentifier = self.__getIdentifier("form", form["rep_value"],form["lexicalFormID"])

			self.g.add((lexicalEntryIdentifier,URIRef(ONTOLEX + form["type"]),lexicalFormIdentifier))
			self.g.add((lexicalEntryIdentifier,RDFS.label,Literal(form["lex_value"], lang=form["iso_639_1"])))
			self.g.add((lexicalFormIdentifier,RDF.type,ONTOLEX.Form))
			self.g.add((lexicalFormIdentifier,ONTOLEX.writtenRep,Literal(form["rep_value"], lang=form["iso_639_1"])))
			self.g.add((lexicalFormIdentifier,RDFS.label,Literal(form["rep_value"], lang=form["iso_639_1"])))


	def printGraph(self):
		print(bytes.decode(self.g.serialize(format=self.format)))


	def __getIdentifier(self,ns,value,id):
		return URIRef( "urn:" + ns + "_" + value + "_" + str(id) )
