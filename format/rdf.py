# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import SKOS, RDFS, RDF, XSD, VOID
from rdflib import Graph

ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
LEXINFO = Namespace("http://www.lexinfo.net/ontology/2.0/lexinfo#")
LIME = Namespace("http://www.w3.org/ns/lemon/lime#")
SKOSTHES = Namespace("http://purl.org/iso25964/skos-thes#")

class RDFGraph:
	def __init__(self,name,language,format,buildlexicon):
		global ONTOLEX
		global LEXINFO
		global LIME
		global SKOSTHES

		self.name = name
		self.language = language
		self.format = format
		self.buildlexicon = buildlexicon
		self.g = Graph()
		self.g.bind("ontolex", ONTOLEX)
		self.g.bind("lexinfo", LEXINFO)
		self.g.bind("skos", SKOS)
		self.g.bind("skosthes", SKOSTHES)

		if buildlexicon:
			self.g.bind("lime", LIME)
			self.g.bind("void", VOID)
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
				
				elif reference["namespace"] == "skos-thes":
					self.g.add((lexicalSenseIdentifier,URIRef(SKOSTHES + reference["property"]),URIRef(reference["reference"])))


	def setInverses(self):
		for s,p,o in self.g.triples( (None, SKOS.broader, None) ):
			self.g.add((o,SKOS.narrower,s))

		for s,p,o in self.g.triples( (None, SKOSTHES.broaderPartitive, None) ):
			self.g.add((o,SKOSTHES.narrowerPartitive,s))

		for s,p,o in self.g.triples( (None, SKOSTHES.broaderInstantial, None) ):
			self.g.add((o,SKOSTHES.narrowerInstantial,s))


	def setRedundants(self):
		""" Not setting inverse relations, so if you want those, execute this before setInverses. """
		for s,p,o in self.g.triples( (None, ONTOLEX.canonicalForm, None) ):
			self.g.add((s,ONTOLEX.lexicalForm,o))

		for s,p,o in self.g.triples( (None, ONTOLEX.otherForm, None) ):
			self.g.add((s,ONTOLEX.lexicalForm,o))

		for s,p,o in self.g.triples( (None, SKOSTHES.broaderPartitive, None) ):
			self.g.add((s,SKOS.broader,o))

		for s,p,o in self.g.triples( (None, SKOSTHES.broaderInstantial, None) ):
			self.g.add((s,SKOS.broader,o))
		
		for s,p,o in self.g.triples( (None, ONTOLEX.writtenRep, None) ):
			self.g.add((s,RDFS.label,o))


	def printGraph(self):
		if self.buildlexicon:
			self.g.add((URIRef("urn:" + self.name),VOID.triples,Literal(str(len(self.g)), datatype=XSD.integer)))

		print(bytes.decode(self.g.serialize(format=self.format)))
