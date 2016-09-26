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
