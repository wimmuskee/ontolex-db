# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import SKOS, RDF, XSD, DCTERMS, OWL
from format.rdfgraph import RDFGraph


class SKOSGraph(RDFGraph):
	def __init__(self,name,language,license,buildpackage):
		RDFGraph.__init__(self, name,language,"turtle",license,buildpackage)

		if self.buildpackage:
			self.g.add((URIRef("urn:" + name),RDF.type,SKOS.ConceptScheme))
			self.g.add((URIRef("urn:" + name),DCTERMS.language,URIRef("http://id.loc.gov/vocabulary/iso639-1/" + language)))


	def setConcepts(self,concepts,conceptLabels,conceptDefinitions):
		for concept in concepts:
			conceptIdentifier = URIRef(concept["sense_identifier"])
			concept_identifier = concept["sense_identifier"]

			self.g.add((conceptIdentifier,RDF.type,SKOS.Concept))
			self.g.add((conceptIdentifier,SKOS.label,Literal(conceptLabels[concept["lexicalEntryID"]], lang=self.language)))
			if concept_identifier in conceptDefinitions:
				self.g.add((conceptIdentifier,SKOS.definition,Literal(conceptDefinitions[concept_identifier], lang=self.language)))
			if self.buildpackage:
				self.g.add((conceptIdentifier,SKOS.inScheme,URIRef("urn:" + self.name)))


	def setConceptRelations(self,conceptrelations):
		SKOSTHES = Namespace("http://purl.org/iso25964/skos-thes#")
		
		for reference in conceptrelations:
			conceptidentifier = URIRef(reference["sense_identifier"])
			if reference["namespace"] == "skos":
				self.g.add((conceptidentifier,URIRef(SKOS + reference["property"]),URIRef(reference["reference"])))
			
			elif reference["namespace"] == "skos-thes":
				self.g.add((conceptidentifier,URIRef(SKOSTHES + reference["property"]),URIRef(reference["reference"])))

			if reference["namespace"] == "ontolex" and reference["property"] == "reference":
				self.g.add((conceptidentifier,DCTERMS.identifier,URIRef(reference["reference"])))
			
			if reference["namespace"] == "lexinfo" and reference["property"] == "synonym":
				self.g.add((conceptidentifier,OWL.sameAs,URIRef(reference["reference"])))


