# -*- coding: utf-8 -*-

def getConfig(parserArgs):
	""" Get config path from args or use default. Return loaded dict."""
	import json
	configpath = validateInput(parserArgs,"config")

	if not configpath:
		configpath = "config.json"

	with open(configpath) as f:
		return json.loads(f.read())


def validateInput(parserArgs,key,default=""):
	""" Simple validation for a parser argument. Return value only when non empty value is found for key. """
	if not parserArgs[key] is None:
		value = parserArgs[key][0].strip(' \t\n\r')
		
		if value:
			return value

	return default

def readBulkCsv(csvfile):
	""" Read bulk input csv file, and return data dictionary. """
	import csv
	with open(csvfile, 'r') as csvfile:
		spamreader = csv.reader(csvfile, delimiter=',')
		headers = spamreader.__next__()
		data = []
		for row in spamreader:
			rowdata = {}
			for i in range(0,len(headers)):
				headername = headers[i]
				value = row[i]
				rowdata[headername] = value
			data.append(rowdata)
	return data
