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
		self.language = language
		self.format = format
		self.buildlexicon = buildlexicon
		self.g = Graph()
		self.g.bind("ontolex", ONTOLEX)
		self.g.bind("lexinfo", LEXINFO)
		self.g.bind("skos", SKOS)

		if buildlexicon:
			self.g.bind("lime", LIME)
			self.g.add((URIRef("urn:" + name),RDF.type,LIME.lexicon))
			self.g.add((URIRef("urn:" + name),LIME.language,Literal(language)))


	def setLexicalEntries(self,lexicalEntries):
		if self.buildlexicon:
			self.g.add((URIRef("urn:" + self.name),LIME.lexicalEntries,Literal(str(len(lexicalEntries)), datatype=XSD.integer)))

		for entry in lexicalEntries:
			lexicalEntryIdentifier = URIRef(entry["lex_identifier"])

			self.g.add((lexicalEntryIdentifier,RDF.type,ONTOLEX.LexicalEntry))
			self.g.add((lexicalEntryIdentifier,RDF.type,URIRef(ONTOLEX + entry["class"])))
			self.g.add((lexicalEntryIdentifier,LEXINFO.partOfSpeech,URIRef(LEXINFO + entry["pos_value"])))
			if self.buildlexicon:
				self.g.add((URIRef("urn:" + self.name),LIME.entry,lexicalEntryIdentifier))



	def setLexicalForms(self,lexicalForms):
		for form in lexicalForms:
			lexicalEntryIdentifier = URIRef(form["lex_identifier"])
			lexicalFormIdentifier = URIRef(form["form_identifier"])

			self.g.add((lexicalEntryIdentifier,URIRef(ONTOLEX + form["type"]),lexicalFormIdentifier))
			if form["type"] == "canonicalForm":
				self.g.add((lexicalEntryIdentifier,RDFS.label,Literal(form["rep_value"], lang=self.language)))

			self.g.add((lexicalFormIdentifier,RDF.type,ONTOLEX.Form))
			self.g.add((lexicalFormIdentifier,ONTOLEX.writtenRep,Literal(form["rep_value"], lang=self.language)))
			self.g.add((lexicalFormIdentifier,RDFS.label,Literal(form["rep_value"], lang=self.language)))


	def setLexicalProperties(self,lexicalProperties):
		for form in lexicalProperties:
			lexicalFormIdentifier = URIRef(form["form_identifier"])

			if form["properties"]:
				for property in form["properties"]:
					self.g.add((lexicalFormIdentifier,URIRef(LEXINFO + property["property"]),URIRef(LEXINFO + property["value"])))


	def setLexicalSenses(self,lexicalSenses,lexicalEntryLabels):
		for sense in lexicalSenses:
			lexicalEntryIdentifier = URIRef(sense["lex_identifier"])
			lexicalSenseIdentifier = URIRef(sense["sense_identifier"])

			self.g.add((lexicalEntryIdentifier,ONTOLEX.sense,lexicalSenseIdentifier))
			self.g.add((lexicalSenseIdentifier,RDF.type,ONTOLEX.LexicalSense))
			self.g.add((lexicalSenseIdentifier,RDF.type,SKOS.Concept))
			self.g.add((lexicalSenseIdentifier,SKOS.label,Literal(lexicalEntryLabels[sense["lexicalEntryID"]], lang=self.language)))


	def setSenseReferences(self,senseReferences):
		for senseref in senseReferences:
			lexicalSenseIdentifier = URIRef(senseref["sense_identifier"])
			for reference in senseref["references"]:
				if reference["namespace"] == "ontolex":
					self.g.add((lexicalSenseIdentifier,URIRef(ONTOLEX + reference["property"]),URIRef(reference["reference"])))

				elif reference["namespace"] == "skos":
					self.g.add((lexicalSenseIdentifier,URIRef(SKOS + reference["property"]),URIRef(reference["reference"])))


	def setRedundants(self):
		for s,p,o in self.g.triples( (None,  SKOS.broader, None) ):
			self.g.add((o,SKOS.narrower,s))

		for s,p,o in self.g.triples( (None,  ONTOLEX.evokes, None) ):
			self.g.add((o,ONTOLEX.isEvokedBy,s))


	def printGraph(self):
		print(bytes.decode(self.g.serialize(format=self.format)))
