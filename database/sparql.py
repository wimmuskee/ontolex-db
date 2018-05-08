# -*- coding: utf-8 -*-

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import SKOS, RDFS, RDF, XSD
from format.namespace import *
import prettytable


class RDFStore:
	def __init__(self,config):
		self.g = Graph()
		self.g.parse("export.ttl",format="turtle")

	def tablePrint(self,method):
		method_to_call = getattr(self, method)
		result = method_to_call()

		x = prettytable.PrettyTable(result.vars)
		for row in result:
			x.add_row([str(row[0]), str(row[1]), str(row[2])])
		print(x)


	def verbComponentsPrefix(self):
		""" Select all adverb prefixes used as a component for verbs. """
		res = self.g.query( """SELECT ?componentID ?label (COUNT(?componentID) as ?count) WHERE {
			?lexicalEntryID rdf:_1 ?componentID .
			?componentID decomp:correspondsTo ?componentEntryID .
			?componentEntryID lexinfo:partOfSpeech lexinfo:adverb ;
				rdfs:label ?label .}
			GROUP BY ?componentID
			ORDER BY DESC(?count)""" )
		return res
