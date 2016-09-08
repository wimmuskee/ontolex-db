# -*- coding: utf-8 -*-

from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import SKOS, RDFS, RDF
from rdflib import Graph

ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
LEXINFO = Namespace("http://www.lexinfo.net/ontology/2.0/lexinfo#")

class RDFGraph:
	def __init__(self,format):
		global ONTOLEX
		global LEXINFO
		global RDF

		self.format = format
		self.g = Graph()
		self.g.bind("ontolex", ONTOLEX)
		self.g.bind("lexinfo", LEXINFO)


	def setLexicalEntries(self,lexicalEntries):
		for entry in lexicalEntries:
			subject = URIRef(entry["identifier"])
			self.g.add((subject,RDF.type,ONTOLEX.lexicalEntry))
			self.g.add((subject,RDF.type,URIRef(ONTOLEX + entry["class"])))
			self.g.add((subject,LEXINFO.partOfSpeech,URIRef(LEXINFO + entry["pos_value"])))


	def printGraph(self):
		print(bytes.decode(self.g.serialize(format=self.format)))
