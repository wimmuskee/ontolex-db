#!/usr/bin/python
# -*- coding: utf-8 -*-

# Retrieves all forms from the exported turtle file and stores them in forms.txt.

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDFS, RDF

g = Graph()
g.parse("../export.ttl", format="turtle")

with open("forms.txt", "w") as f:
	for lexicalFormID in g.subjects(RDF.type,URIRef("http://www.w3.org/ns/lemon/ontolex#Form")):
		f.write(str(g.value(lexicalFormID,RDFS.label,None)) + "\n")
