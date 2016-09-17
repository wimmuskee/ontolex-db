# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import SKOS, RDF, XSD, DCTERMS
from rdflib import Graph

SKOSTHES = Namespace("http://purl.org/iso25964/skos-thes#")


class SKOSGraph:
	def __init__(self,name,language):
		global SKOSTHES

		self.name = name
		self.language = language
		self.g = Graph()
		self.g.bind("skos", SKOS)
		self.g.bind("dct", DCTERMS)
		self.g.bind("skosthes", SKOSTHES)
		self.g.add((URIRef("urn:" + name),RDF.type,SKOS.ConceptScheme))
		self.g.add((URIRef("urn:" + name),DCTERMS.language,Literal(language)))


	def setConcepts(self,concepts,conceptLabels):
		for concept in concepts:
			conceptidentifier = URIRef(concept["sense_identifier"])

			self.g.add((conceptidentifier,RDF.type,SKOS.Concept))
			self.g.add((conceptidentifier,SKOS.inScheme,URIRef("urn:" + self.name)))
			self.g.add((conceptidentifier,SKOS.label,Literal(conceptLabels[concept["lexicalEntryID"]], lang=self.language)))


	def setConceptRelations(self,conceptrelations):
		for conceptrel in conceptrelations:
			conceptidentifier = URIRef(conceptrel["sense_identifier"])
			for reference in conceptrel["references"]:
				if reference["namespace"] == "skos":
					self.g.add((conceptidentifier,URIRef(SKOS + reference["property"]),URIRef(reference["reference"])))
				
				elif reference["namespace"] == "skos-thes":
					self.g.add((conceptidentifier,URIRef(SKOSTHES + reference["property"]),URIRef(reference["reference"])))

				if reference["namespace"] == "ontolex" and reference["property"] == "reference":
					self.g.add((conceptidentifier,DCTERMS.identifier,URIRef(reference["reference"])))


	def setInverses(self):
		for s,p,o in self.g.triples( (None, SKOS.broader, None) ):
			self.g.add((o,SKOS.narrower,s))

		for s,p,o in self.g.triples( (None, SKOSTHES.broaderPartitive, None) ):
			self.g.add((o,SKOSTHES.narrowerPartitive,s))

		for s,p,o in self.g.triples( (None, SKOSTHES.broaderInstantial, None) ):
			self.g.add((o,SKOSTHES.narrowerInstantial,s))


	def setRedundants(self):
		""" Not setting inverse relations, so if you want those, execute this before setInverses. """
		for s,p,o in self.g.triples( (None, SKOSTHES.broaderPartitive, None) ):
			self.g.add((s,SKOS.broader,o))

		for s,p,o in self.g.triples( (None, SKOSTHES.broaderInstantial, None) ):
			self.g.add((s,SKOS.broader,o))



	def printGraph(self):
		print(bytes.decode(self.g.serialize(format="turtle")))