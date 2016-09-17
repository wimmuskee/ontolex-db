# -*- coding: utf-8 -*-

from rdflib import Graph
from rdflib.namespace import XSD, VOID, SKOS
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

		if self.buildpackage:
			self.g.bind("void", VOID)


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
		if self.buildpackage:
			self.g.add((URIRef("urn:" + self.name),VOID.triples,Literal(str(len(self.g)), datatype=XSD.integer)))

		print(bytes.decode(self.g.serialize(format=self.format)))
