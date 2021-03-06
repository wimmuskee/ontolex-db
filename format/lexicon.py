# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal
from rdflib.namespace import RDFS, RDF, XSD
from format.rdfgraph import RDFGraph
from format.namespace import *


class LexiconGraph(RDFGraph):
	def __init__(self,exportconfig,language,format,buildpackage,persist):
		RDFGraph.__init__(self,exportconfig,language,format,buildpackage,persist)

		self.g.bind("ontolex", ONTOLEX)
		self.g.bind("lexinfo", LEXINFO)
		self.g.bind("decomp", DECOMP)
		self.g.bind("isocat", ISOCAT)

		if self.buildpackage:
			self.g.bind("lime", LIME)
			self.g.add((URIRef("urn:" + exportconfig["name"]),RDF.type,LIME.lexicon))
			self.g.add((URIRef("urn:" + exportconfig["name"]),LIME.language,URIRef("http://id.loc.gov/vocabulary/iso639-1/" + language)))


	def setLexicalEntries(self,lexicalEntries):
		if self.buildpackage:
			self.g.add((URIRef("urn:" + self.exportconfig["name"]),LIME.lexicalEntries,Literal(str(len(lexicalEntries)), datatype=XSD.integer)))

		for entry in lexicalEntries:
			lexicalEntryIdentifier = URIRef(entry["lex_identifier"])

			self.g.add((lexicalEntryIdentifier,RDF.type,ONTOLEX.LexicalEntry))
			self.g.add((lexicalEntryIdentifier,RDF.type,URIRef(ONTOLEX + entry["class"])))
			self.g.add((lexicalEntryIdentifier,LEXINFO.partOfSpeech,URIRef(LEXINFO + entry["pos_value"])))
			if self.buildpackage:
				self.g.add((URIRef("urn:" + self.exportconfig["name"]),LIME.entry,lexicalEntryIdentifier))


	def setLexicalEntryRelatons(self,lexicalEntryRelations):
		for relation in lexicalEntryRelations:
			lexicalEntryIdentifier = URIRef(relation["lex_identifier"])
			
			self.g.add((lexicalEntryIdentifier,URIRef(relation["relation"]),URIRef(relation["reference"])))
			# for lexinfo contraction forms
			if relation["relation"][-3:] == "For":
				self.g.add((lexicalEntryIdentifier,RDF.type,URIRef(relation["relation"][:-3])))


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
			self.g.add((lexicalSenseIdentifier,RDFS.label,Literal(lexicalEntryLabels[sense["lexicalEntryID"]], lang=self.language)))
			if sense_identifier in lexicalSenseDefinitions:
				self.g.add((lexicalSenseIdentifier,LEXINFO.explanation,Literal(lexicalSenseDefinitions[sense_identifier], lang=self.language)))


	def setSenseReferences(self,senseReferences):
		for reference in senseReferences:
			lexicalSenseIdentifier = URIRef(reference["sense_identifier"])
			if reference["namespace"] == "ontolex":
				self.g.add((lexicalSenseIdentifier,URIRef(ONTOLEX + reference["property"]),URIRef(reference["reference"])))

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
		RDFGraph.setSynonyms(self,LEXINFO.synonym,[str(LEXINFO.hypernym),str(LEXINFO.relatedTerm),str(LEXINFO.antonym)])

		for s,p,o in self.g.triples( (None, LEXINFO.antonym, None) ):
			self.g.add((o,LEXINFO.antonym,s))

		for s,p,o in self.g.triples( (None, LEXINFO.relatedTerm, None) ):
			self.g.add((o,LEXINFO.relatedTerm,s))

		for s,p,o in self.g.triples( (None, LEXINFO.hypernym, None) ):
			self.g.add((o,LEXINFO.hyponym,s))


	def setRedundants(self):
		""" Not setting inverse relations, so if you want those, execute this before setInverses. """
		RDFGraph.setRedundants(self)

		for s,p,o in self.g.triples( (None, ONTOLEX.canonicalForm, None) ):
			self.g.add((s,ONTOLEX.lexicalForm,o))

		for s,p,o in self.g.triples( (None, ONTOLEX.otherForm, None) ):
			self.g.add((s,ONTOLEX.lexicalForm,o))

		for s,p,o in self.g.triples( (None, ONTOLEX.writtenRep, None) ):
			self.g.add((s,RDFS.label,o))

		for s,p,o in self.g.triples( (None, LEXINFO.acronymFor, None) ):
			self.g.add((s,LEXINFO.contractionFor,o))
			self.g.add((s,RDF.type,LEXINFO.contraction))

		for s,p,o in self.g.triples( (None, LEXINFO.initialismFor, None) ):
			self.g.add((s,LEXINFO.contractionFor,o))
			self.g.add((s,RDF.type,LEXINFO.contraction))

		for s,p,o in self.g.triples( (None, LEXINFO.abbreviationFor, None) ):
			self.g.add((s,LEXINFO.contractionFor,o))
			self.g.add((s,RDF.type,LEXINFO.contraction))

		for s,p,o in self.g.triples( (None,LEXINFO.partOfSpeech,LEXINFO.presentParticipleAdjective) ):
			self.g.add((s,LEXINFO.partOfSpeech,LEXINFO.adjective))

		for s,p,o in self.g.triples( (None,LEXINFO.partOfSpeech,LEXINFO.pastParticipleAdjective) ):
			self.g.add((s,LEXINFO.partOfSpeech,LEXINFO.adjective))

		for s,p,o in self.g.triples( (None,LEXINFO.partOfSpeech,LEXINFO.ordinalAdjective) ):
			self.g.add((s,LEXINFO.partOfSpeech,LEXINFO.adjective))

		for s,p,o in self.g.triples( (None,LEXINFO.partOfSpeech,LEXINFO.cardinalNumeral) ):
			self.g.add((s,LEXINFO.partOfSpeech,LEXINFO.numeral))

		for s,p,o in self.g.triples( (None,LEXINFO.partOfSpeech,LEXINFO.indefiniteCardinalNumeral) ):
			self.g.add((s,LEXINFO.partOfSpeech,LEXINFO.numeral))

		for s,p,o in self.g.triples( (None,LEXINFO.partOfSpeech,LEXINFO.indefiniteOrdinalNumeral) ):
			self.g.add((s,LEXINFO.partOfSpeech,LEXINFO.numeral))


	def setTransitives(self):
		RDFGraph.setTransitives(self,LEXINFO.relatedTerm)
