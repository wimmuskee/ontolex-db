# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import SKOS, RDF, XSD, DCTERMS, OWL
from format.rdfgraph import RDFGraph


class SKOSGraph(RDFGraph):
	def __init__(self,name,language,exportconfig,buildpackage,persist):
		RDFGraph.__init__(self, name,language,"turtle",exportconfig,buildpackage,persist)

		self.g.bind("skos", SKOS)
		self.g.bind("owl", OWL)

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
		for reference in conceptrelations:
			conceptidentifier = URIRef(reference["sense_identifier"])
			if reference["namespace"] == "ontolex" and reference["property"] == "reference":
				self.g.add((conceptidentifier,SKOS.exactMatch,URIRef(reference["reference"])))
			
			if reference["namespace"] == "lexinfo" and reference["property"] == "synonym":
				self.g.add((conceptidentifier,OWL.sameAs,URIRef(reference["reference"])))

			if reference["namespace"] == "lexinfo" and reference["property"] == "relatedTerm":
				self.g.add((conceptidentifier,SKOS.related,URIRef(reference["reference"])))

			if reference["namespace"] == "lexinfo" and reference["property"] == "hypernym":
				self.g.add((conceptidentifier,SKOS.broaderTransitive,URIRef(reference["reference"])))


	def setInverses(self):
		RDFGraph.setSynonyms(self,OWL.sameAs,[str(SKOS.related),str(SKOS.broaderTransitive)])

		for s,p,o in self.g.triples( (None, SKOS.related, None) ):
			self.g.add((o,SKOS.related,s))

		for s,p,o in self.g.triples( (None, SKOS.broaderTransitive, None) ):
			self.g.add((o,SKOS.narrowerTransitive,s))


	def setTransitives(self):
		RDFGraph.setTransitives(self,SKOS.related)
