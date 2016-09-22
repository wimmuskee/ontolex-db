# -*- coding: utf-8 -*-

def validateInput(parserArgs,key):
	""" Simple validation for a parser argument. Return value only when non empty value is found for key. """
	if not parserArgs[key] is None:
		value = parserArgs[key][0].strip(' \t\n\r')
		
		if value:
			return value

	return ""
