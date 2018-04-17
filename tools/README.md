# ontolex-db tools
In this directory you can find a couple of practical tools for adding new words.
As these tools do not work from the database, remember to make a fresh turtle export before commencing with gathering missing words and adding those.

## exportAllForms.py
Retrieves all forms from the exported turtle file and stores them in forms.txt.

## selectMissingTerms.sh
Select all alphanumeric single words from a file and compare them to the file with all forms (forms.txt). 
Output all words that have not been found.

## batchAdd.sh
Select random words from a provided wordlist, and add them as noun, adjective or verb.
