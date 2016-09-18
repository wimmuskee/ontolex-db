# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import SKOS, RDFS, RDF, XSD
from format.rdfgraph import RDFGraph


class LexiconGraph(RDFGraph):
	def __init__(self,name,language,format,buildpackage):
		RDFGraph.__init__(self, name,language,format,buildpackage)

		global ONTOLEX
		global LEXINFO
		global SKOSTHES
		ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
		LEXINFO = Namespace("http://www.lexinfo.net/ontology/2.0/lexinfo#")
		SKOSTHES = Namespace("http://purl.org/iso25964/skos-thes#")
		self.g.bind("ontolex", ONTOLEX)
		self.g.bind("lexinfo", LEXINFO)

		if self.buildpackage:
			global LIME
			LIME = Namespace("http://www.w3.org/ns/lemon/lime#")
			self.g.bind("lime", LIME)
			self.g.add((URIRef("urn:" + name),RDF.type,LIME.lexicon))
			self.g.add((URIRef("urn:" + name),LIME.language,Literal(language)))


	def setLexicalEntries(self,lexicalEntries):
		if self.buildpackage:
			self.g.add((URIRef("urn:" + self.name),LIME.lexicalEntries,Literal(str(len(lexicalEntries)), datatype=XSD.integer)))

		for entry in lexicalEntries:
			lexicalEntryIdentifier = URIRef(entry["lex_identifier"])

			self.g.add((lexicalEntryIdentifier,RDF.type,ONTOLEX.LexicalEntry))
			self.g.add((lexicalEntryIdentifier,RDF.type,URIRef(ONTOLEX + entry["class"])))
			self.g.add((lexicalEntryIdentifier,LEXINFO.partOfSpeech,URIRef(LEXINFO + entry["pos_value"])))
			if self.buildpackage:
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
			self.g.add((lexicalSenseIdentifier,RDFS.label,Literal(lexicalEntryLabels[sense["lexicalEntryID"]], lang=self.language)))


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

				elif reference["namespace"] == "lexinfo":
					self.g.add((lexicalSenseIdentifier,URIRef(LEXINFO + reference["property"]),URIRef(reference["reference"])))


	def setInverses(self):
		RDFGraph.setInverses(self)

		for s,p,o in self.g.triples( (None, LEXINFO.antonym, None) ):
			self.g.add((o,LEXINFO.antonym,s))


	def setRedundants(self):
		""" Not setting inverse relations, so if you want those, execute this before setInverses. """
		RDFGraph.setRedundants(self)

		for s,p,o in self.g.triples( (None, ONTOLEX.canonicalForm, None) ):
			self.g.add((s,ONTOLEX.lexicalForm,o))

		for s,p,o in self.g.triples( (None, ONTOLEX.otherForm, None) ):
			self.g.add((s,ONTOLEX.lexicalForm,o))

		for s,p,o in self.g.triples( (None, ONTOLEX.writtenRep, None) ):
			self.g.add((s,RDFS.label,o))
