# ontolex-db
A tool to manage your ontolex based dictionary.

# usage
The examples below assume language *nl*, and export responses are truncated and commented.

# adding words and relations
Words and relations can be added to the database using the commandline tools.
```bash
ontolex-db-manager add entry -w fiets -p noun
```
Use the export function to see the identifiers for adding relations.
```bash
ontolex-db-export -v fiets -p noun

# <urn:uuid:8dd2b472-73de-4490-9543-73d636c126f2> a ontolex:LexicalEntry,
#        ontolex:Word ;
#    rdfs:label "fiets"@nl ;
#    lexinfo:partOfSpeech lexinfo:noun ;
#    ontolex:canonicalForm <urn:uuid:e2983ddc-77d1-40ac-b9c9-16f35d28e8a0> .
#
# <urn:uuid:e2983ddc-77d1-40ac-b9c9-16f35d28e8a0> a ontolex:Form ;
#    ontolex:writtenRep "fiets"@nl .

ontolex-db-manager add form -s urn:uuid:8dd2b472-73de-4490-9543-73d636c126f2 -w fietsen
ontolex-db-export -v fiets -p noun

# <urn:uuid:8dd2b472-73de-4490-9543-73d636c126f2> a ontolex:LexicalEntry,
#        ontolex:Word ;
#    rdfs:label "fiets"@nl ;
#    lexinfo:partOfSpeech lexinfo:noun ;
#    ontolex:canonicalForm <urn:uuid:e2983ddc-77d1-40ac-b9c9-16f35d28e8a0> ;
#    ontolex:otherForm <urn:uuid:36f1dd6c-e264-4f1a-b3a9-4238cfeb5244> .
#
# <urn:uuid:e2983ddc-77d1-40ac-b9c9-16f35d28e8a0> a ontolex:Form ;
#    ontolex:writtenRep "fiets"@nl .
#
# <urn:uuid:36f1dd6c-e264-4f1a-b3a9-4238cfeb5244> a ontolex:Form ;
#    ontolex:writtenRep "fietsen"@nl .

ontolex-db-manager add formprops -s urn:uuid:e2983ddc-77d1-40ac-b9c9-16f35d28e8a0 -f number:singular
ontolex-db-manager add formprops -s urn:uuid:36f1dd6c-e264-4f1a-b3a9-4238cfeb5244 -f number:plural
```
