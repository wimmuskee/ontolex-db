# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import SKOS, RDF, XSD, DCTERMS
from format.rdfgraph import RDFGraph


class SKOSGraph(RDFGraph):
	def __init__(self,name,language,buildpackage):
		RDFGraph.__init__(self, name,language,"turtle",buildpackage)

		self.g.bind("dct", DCTERMS)

		if self.buildpackage:
			self.g.add((URIRef("urn:" + name),RDF.type,SKOS.ConceptScheme))
			self.g.add((URIRef("urn:" + name),DCTERMS.language,Literal(language)))


	def setConcepts(self,concepts,conceptLabels):
		for concept in concepts:
			conceptidentifier = URIRef(concept["sense_identifier"])

			self.g.add((conceptidentifier,RDF.type,SKOS.Concept))
			self.g.add((conceptidentifier,SKOS.label,Literal(conceptLabels[concept["lexicalEntryID"]], lang=self.language)))
			if self.buildpackage:
				self.g.add((conceptidentifier,SKOS.inScheme,URIRef("urn:" + self.name)))


	def setConceptRelations(self,conceptrelations):
		SKOSTHES = Namespace("http://purl.org/iso25964/skos-thes#")
		
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
		RDFGraph.setInverses(self)

	def setRedundants(self):
		RDFGraph.setRedundants(self)
