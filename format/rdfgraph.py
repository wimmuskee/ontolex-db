# -*- coding: utf-8 -*-

from rdflib import Graph
from rdflib.namespace import XSD, VOID, DCTERMS
from rdflib import URIRef, Literal, Namespace


class RDFGraph():
	def __init__(self,name,language,format,exportconfig,buildpackage,persist):
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

		if self.buildpackage:
			self.g.bind("dct", DCTERMS)
			self.g.bind("void", VOID)


	def setSynonyms(self,synonymPredicate,synonymCopy):
		""" Merge specific relations from synonym concepts. Those relations that should be merged are
		provided by the synonymCopy list. """
		for s,p,o in self.g.triples((None,synonymPredicate,None)):
			# set prelimenary findings to temp, not actual, to prevent double copies, and endless transitive loops
			# copy relations from each s,o to eachother, and deal with inverses of those later
			tempg = Graph()

			for s2,p2,o2 in self.g.triples((s,None,None)):
				if str(p2) in synonymCopy:
					tempg.add((o,p2,o2))
			for s2,p2,o2 in self.g.triples((o,None,None)):
				if str(p2) in synonymCopy:
					tempg.add((s,p2,o2))

			for s2,p2,o2 in tempg:
				self.g.add((s2,p2,o2))

			self.g.add((o,synonymPredicate,s))


	def setRedundants(self):
		""" Not setting inverse relations, so if you want those, execute this before setInverses. """
		pass


	def setTransitives(self,relatedPredicate):
		""" This function is dependent on setInverses and setRedundants """
		""" This specifically sets all related terms to each other as well,
		so if a -> b and b -> c, then a -> c ."""
		relatedlist = set()
		for subject,object in self.g.subject_objects(relatedPredicate):
			relatedlist.add(str(subject))

		for concept in list(relatedlist):
			corners = []
			# we are removing elements from relatedlist while iterating
			# make sure the concept still exists before getting corners
			if concept in relatedlist:
				corners = self.__getCorners(concept,relatedPredicate)

			for corner in corners:
				relatedlist.remove(corner)

			for x in corners:
				for y in corners:
					if x != y:
						self.g.add((URIRef(x),relatedPredicate,URIRef(y)))
						self.g.add((URIRef(y),relatedPredicate,URIRef(x)))


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


	def __getCorners(self,concept,relatedPredicate,corners=None,checked=None):
		""" Used for getting all related concepts that are connected somehow. """
		if not corners:
			corners = []
		if not checked:
			checked = []

		# add to checked
		checked.append(concept)

		# add to corners
		corners.append(concept)

		for related in self.g.objects(URIRef(concept),relatedPredicate):
			related_str = str(related)
			if related_str and related_str not in checked:
				corners = self.__getCorners(related_str,relatedPredicate,corners,checked)

		return corners
