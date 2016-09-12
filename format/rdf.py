# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import SKOS, RDFS, RDF, XSD
from rdflib import Graph

ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
LEXINFO = Namespace("http://www.lexinfo.net/ontology/2.0/lexinfo#")
LIME = Namespace("http://www.w3.org/ns/lemon/lime#")


class RDFGraph:
	def __init__(self,name,language,format,buildlexicon):
		global ONTOLEX
		global LEXINFO
		global LIME

		self.name = name
		self.format = format
		self.buildlexicon = buildlexicon
		self.g = Graph()
		self.g.bind("ontolex", ONTOLEX)
		self.g.bind("lexinfo", LEXINFO)
		if buildlexicon:
			self.g.bind("lime", LIME)
			self.g.add((URIRef("urn:" + name),RDF.type,LIME.lexicon))
			self.g.add((URIRef("urn:" + name),LIME.language,Literal(language)))


	def setLexicalEntries(self,lexicalEntries):
		if self.buildlexicon:
			self.g.add((URIRef("urn:" + self.name),LIME.lexicalEntries,Literal(str(len(lexicalEntries)), datatype=XSD.integer)))

		for entry in lexicalEntries:
			lexicalEntryIdentifier = self.__getIdentifier("lex",entry["lex_value"],entry["lexicalEntryID"])

			self.g.add((lexicalEntryIdentifier,RDF.type,ONTOLEX.lexicalEntry))
			self.g.add((lexicalEntryIdentifier,RDF.type,URIRef(ONTOLEX + entry["class"])))
			self.g.add((lexicalEntryIdentifier,LEXINFO.partOfSpeech,URIRef(LEXINFO + entry["pos_value"])))
			if self.buildlexicon:
				self.g.add((URIRef("urn:" + self.name),LIME.entry,lexicalEntryIdentifier))



	def setLexicalForms(self,lexicalForms):
		for form in lexicalForms:
			lexicalEntryIdentifier = self.__getIdentifier("lex",form["lex_value"],form["lexicalEntryID"])
			lexicalFormIdentifier = self.__getIdentifier("form", form["rep_value"],form["lexicalFormID"])

			self.g.add((lexicalEntryIdentifier,URIRef(ONTOLEX + form["type"]),lexicalFormIdentifier))
			self.g.add((lexicalEntryIdentifier,RDFS.label,Literal(form["lex_value"], lang=form["iso_639_1"])))
			self.g.add((lexicalFormIdentifier,RDF.type,ONTOLEX.Form))
			self.g.add((lexicalFormIdentifier,ONTOLEX.writtenRep,Literal(form["rep_value"], lang=form["iso_639_1"])))
			self.g.add((lexicalFormIdentifier,RDFS.label,Literal(form["rep_value"], lang=form["iso_639_1"])))


	def setLexicalProperties(self,lexicalProperties):
		for form in lexicalProperties:
			lexicalFormIdentifier = self.__getIdentifier("form", form["rep_value"],form["lexicalFormID"])
			if form["properties"]:
				for property in form["properties"]:
					self.g.add((lexicalFormIdentifier,URIRef(LEXINFO + property["property"]),URIRef(LEXINFO + property["value"])))


	def printGraph(self):
		print(bytes.decode(self.g.serialize(format=self.format)))


	def __getIdentifier(self,ns,value,id):
		return URIRef( "urn:" + ns + "_" + value + "_" + str(id) )
