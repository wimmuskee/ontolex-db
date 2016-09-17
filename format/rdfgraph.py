# -*- coding: utf-8 -*-

from rdflib import Graph
from rdflib.namespace import XSD, VOID, SKOS, DCTERMS
from rdflib import URIRef, Literal, Namespace


class RDFGraph():
	def __init__(self,name,language,format,buildpackage):
		global SKOSTHES
		SKOSTHES = Namespace("http://purl.org/iso25964/skos-thes#")

		self.name = name
		self.language = language
		self.format = format
		self.buildpackage = buildpackage
		self.g = Graph()
		self.g.bind("skos", SKOS)
		self.g.bind("skosthes", SKOSTHES)
		self.g.bind("dct", DCTERMS)

		if self.buildpackage:
			self.g.bind("void", VOID)


	def setInverses(self):
		for s,p,o in self.g.triples( (None, SKOS.broader, None) ):
			self.g.add((o,SKOS.narrower,s))

		for s,p,o in self.g.triples( (None, SKOS.related, None) ):
			self.g.add((o,SKOS.related,s))

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


	def setTransitives(self,senseIdentifiers):
		""" This function is dependent on setInverses and setRedundants """
		for senseIdentifier in senseIdentifiers:
			for narrowerID in self.g.objects(URIRef(senseIdentifier),SKOS.narrower):
				self.__setTransitive(narrowerID,senseIdentifier)


	def printGraph(self):
		if self.buildpackage:
			import datetime
			self.g.add((URIRef("urn:" + self.name),DCTERMS.date,Literal(str(datetime.date.today()))))
			self.g.add((URIRef("urn:" + self.name),VOID.triples,Literal(str(len(self.g)+1), datatype=XSD.integer)))

		print(bytes.decode(self.g.serialize(format=self.format)))


	def __setTransitive(self,startSenseID,targetSenseID):
		""" Move down the graph, and store transitives (also inverses), and move down again."""
		for narrowerID in self.g.objects(URIRef(startSenseID),SKOS.narrower):
			self.g.add((URIRef(narrowerID),SKOS.broaderTransitive,URIRef(targetSenseID)))
			self.g.add((URIRef(targetSenseID),SKOS.narrowerTransitive,URIRef(narrowerID)))
			self.__setTransitive(narrowerID,targetSenseID)
