# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import SKOS, RDFS, RDF, XSD
from format.rdfgraph import RDFGraph


class LexiconGraph(RDFGraph):
	def __init__(self,name,language,format,license,buildpackage):
		RDFGraph.__init__(self, name,language,format,license,buildpackage)

		global ONTOLEX
		global LEXINFO
		global SKOSTHES
		global DECOMP
		global ISOCAT
		ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
		LEXINFO = Namespace("http://www.lexinfo.net/ontology/2.0/lexinfo#")
		SKOSTHES = Namespace("http://purl.org/iso25964/skos-thes#")
		DECOMP = Namespace("http://www.w3.org/ns/lemon/decomp#")
		ISOCAT = Namespace("http://www.isocat.org/datcat/")

		self.g.bind("ontolex", ONTOLEX)
		self.g.bind("lexinfo", LEXINFO)
		self.g.bind("decomp", DECOMP)
		self.g.bind("isocat", ISOCAT)

		if self.buildpackage:
			global LIME
			LIME = Namespace("http://www.w3.org/ns/lemon/lime#")
			self.g.bind("lime", LIME)
			self.g.add((URIRef("urn:" + name),RDF.type,LIME.lexicon))
			self.g.add((URIRef("urn:" + name),LIME.language,URIRef("http://id.loc.gov/vocabulary/iso639-1/" + language)))


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

			if form["syllableCount"]:
				self.g.add((lexicalFormIdentifier,URIRef(ISOCAT + "DC-499"),Literal(form["syllableCount"], datatype=XSD.integer)))


	def setLexicalProperties(self,lexicalProperties):
		for property in lexicalProperties:
			lexicalFormIdentifier = URIRef(property["form_identifier"])
			self.g.add((lexicalFormIdentifier,URIRef(property["property"]),URIRef(property["value"])))


	def setLexicalSenses(self,lexicalSenses,lexicalEntryLabels,lexicalSenseDefinitions):
		for sense in lexicalSenses:
			lexicalEntryIdentifier = URIRef(sense["lex_identifier"])
			lexicalSenseIdentifier = URIRef(sense["sense_identifier"])
			sense_identifier = sense["sense_identifier"]

			self.g.add((lexicalEntryIdentifier,ONTOLEX.sense,lexicalSenseIdentifier))
			self.g.add((lexicalSenseIdentifier,RDF.type,ONTOLEX.LexicalSense))
			self.g.add((lexicalSenseIdentifier,RDF.type,SKOS.Concept))
			self.g.add((lexicalSenseIdentifier,RDFS.label,Literal(lexicalEntryLabels[sense["lexicalEntryID"]], lang=self.language)))
			if sense_identifier in lexicalSenseDefinitions:
				self.g.add((lexicalSenseIdentifier,SKOS.definition,Literal(lexicalSenseDefinitions[sense_identifier], lang=self.language)))


	def setSenseReferences(self,senseReferences):
		for reference in senseReferences:
			lexicalSenseIdentifier = URIRef(reference["sense_identifier"])
			if reference["namespace"] == "ontolex":
				self.g.add((lexicalSenseIdentifier,URIRef(ONTOLEX + reference["property"]),URIRef(reference["reference"])))

			elif reference["namespace"] == "skos":
				self.g.add((lexicalSenseIdentifier,URIRef(SKOS + reference["property"]),URIRef(reference["reference"])))
			
			elif reference["namespace"] == "skos-thes":
				self.g.add((lexicalSenseIdentifier,URIRef(SKOSTHES + reference["property"]),URIRef(reference["reference"])))

			elif reference["namespace"] == "lexinfo":
				self.g.add((lexicalSenseIdentifier,URIRef(LEXINFO + reference["property"]),URIRef(reference["reference"])))


	def setLexicalComponents(self,lexicalComponents):
		for lexicalComponent in lexicalComponents:
			lexicalEntryID = URIRef(lexicalComponent["lex_identifier"])
			componentID = URIRef(lexicalComponent["comp_identifier"])
			positionPreficate = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#_" + str(lexicalComponent["position"]))

			self.g.add((lexicalEntryID,DECOMP.constituent,componentID))
			self.g.add((lexicalEntryID,positionPreficate,componentID))


	def setComponents(self,components):
		for component in components:
			lexicalEntryID = URIRef(component["lex_identifier"])
			componentID = URIRef(component["comp_identifier"])
			lexicalFormID = URIRef(component["form_identifier"])
			value = str(self.g.value(lexicalFormID,ONTOLEX.writtenRep,None))
			
			self.g.add((componentID,RDF.type,DECOMP.Component))
			self.g.add((componentID,DECOMP.correspondsTo,lexicalEntryID))
			if "rep_value" in component:
				self.g.add((componentID,RDFS.label,Literal(component["rep_value"], lang=self.language)))
			elif value:
				# add the value and look up the lexinfo properties in the graph
				self.g.add((componentID,RDFS.label,Literal(value, lang=self.language)))
				for s,p,o in self.g.triples((lexicalFormID,None,None)):
					if str(p)[:44] == "http://www.lexinfo.net/ontology/2.0/lexinfo#":
						self.g.add((componentID,p,o))


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
