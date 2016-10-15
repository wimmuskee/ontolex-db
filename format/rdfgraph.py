# -*- coding: utf-8 -*-

from rdflib import Graph
from rdflib.namespace import XSD, VOID, SKOS, DCTERMS, OWL
from rdflib import URIRef, Literal, Namespace


class RDFGraph():
	def __init__(self,name,language,format,exportconfig,buildpackage,persist):
		global SKOSTHES
		global OWL
		SKOSTHES = Namespace("http://purl.org/iso25964/skos-thes#")

		self.name = name
		self.language = language
		self.format = format
		self.exportconfig = exportconfig
		self.buildpackage = buildpackage
		
		if persist:
			self.g = Graph("Sleepycat", identifier=self.name)
			if self.g.open(self.exportconfig["persist_base"] + "/" + self.name, create=False) == 1:
				self.g.open(self.exportconfig["persist_base"] + "/" + self.name, create=True)
				self.g.remove((None,None,None))
			else:
				self.g.open(self.exportconfig["persist_base"] + "/" + self.name, create=True)
		else:
			self.g = Graph()

		self.g.bind("skos", SKOS)
		self.g.bind("skosthes", SKOSTHES)
		self.g.bind("dct", DCTERMS)
		self.g.bind("owl", OWL)

		if self.buildpackage:
			self.g.bind("void", VOID)


	def setInverses(self,synonymPredicate):
		synonymCopy = [ str(SKOS.broader), str(SKOSTHES.broaderInstantial), str(SKOSTHES.broaderPartitive) ]
		for s,p,o in self.g.triples((None,synonymPredicate,None)):
			self.g.add((o,synonymPredicate,s))

			# set prelimenary findings to temp, not actual, to prevent double copies, and endless transitive loops
			tempg = Graph()

			# copy relations to subjects/objects
			for s2,p2,o2 in self.g.triples((None,None,s)):
				if str(p2) in synonymCopy:
					tempg.add((s2,p2,o))
			for s2,p2,o2 in self.g.triples((None,None,o)):
				if str(p2) in synonymCopy:
					tempg.add((s2,p2,s))

			# copy relations from subjects/objects
			for s2,p2,o2 in self.g.triples((s,None,None)):
				if str(p2) in synonymCopy:
					tempg.add((o,p2,s2))
			for s2,p2,o2 in self.g.triples((o,None,None)):
				if str(p2) in synonymCopy:
					tempg.add((s,p2,s2))

			for s,p,o in tempg:
				self.g.add((s,p,o))


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


	def setTransitives(self):
		""" This function is dependent on setInverses and setRedundants """
		for senseIdentifier in self.exportconfig["transitiveSenseIdentifiers"]:
			for narrowerID in self.g.objects(URIRef(senseIdentifier),SKOS.narrower):
				self.__setTransitive(narrowerID,senseIdentifier)

			# also set these as topConcepts
			self.g.add((URIRef("urn:" + self.name),SKOS.hasTopConcept,URIRef(senseIdentifier)))
			self.g.add((URIRef(senseIdentifier),SKOS.topConceptOf,URIRef("urn:" + self.name)))


	def printGraph(self):
		if self.buildpackage:
			import datetime
			self.g.add((URIRef("urn:" + self.name),DCTERMS.date,Literal(str(datetime.date.today()))))
			if self.exportconfig["license"]:
				self.g.add((URIRef("urn:" + self.name),DCTERMS.license,Literal(self.exportconfig["license"])))
			if self.exportconfig["creator"]:
				self.g.add((URIRef("urn:" + self.name),DCTERMS.creator,Literal(self.exportconfig["creator"])))
			self.g.add((URIRef("urn:" + self.name),VOID.triples,Literal(str(len(self.g)+1), datatype=XSD.integer)))

		print(bytes.decode(self.g.serialize(format=self.format)))
		self.g.close()


	def __setTransitive(self,startSenseID,targetSenseID):
		""" Move down the graph, and store transitives (also inverses), and move down again."""
		for narrowerID in self.g.objects(URIRef(startSenseID),SKOS.narrower):
			self.g.add((URIRef(narrowerID),SKOS.broaderTransitive,URIRef(targetSenseID)))
			self.g.add((URIRef(targetSenseID),SKOS.narrowerTransitive,URIRef(narrowerID)))
			self.__setTransitive(narrowerID,targetSenseID)
