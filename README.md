# ontolex-db
A tool to manage your ontolex based dictionary.

# installation
No proper installer yet, just pull the repo, set the config.json, and use the sql files in init/ to setup a database and go.

## dependencies
- [rdflib](https://github.com/RDFLib/rdflib)
- [PyMySQL](https://github.com/PyMySQL/PyMySQL)
- [Berkeley DB](http://www.oracle.com/technetwork/database/database-technologies/berkeleydb/overview/index.html)
- [bsddb3](http://pypi.python.org/pypi/bsddb3/)
- [prettytable](https://code.google.com/p/prettytable/)

# usage
The examples below assume language *nl*, and export responses are truncated and commented.

## adding simple words and relations
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

## adding contractions
Various forms of contraction relations can be added between lexicalEntries, namely *abbreviationFor*,
*initialismFor* and *acronymFor*. For instance, adding the full version as well as the initialism
for an entry:
```bash
ontolex-db-manager add entry -w "besloten vennootschap" -p noun
ontolex-db-manager add entry -w "bv" -p noun

# retrieve the lexicalEntryIDs and
ontolex-db-manager add entryrel -s urn:uuid:5ede5896-67a0-4223-bb79-817c646cecd3 -t urn:uuid:5b4c4848-8ad7-429d-88c4-7eb223a5fb5b -r lexinfo:initialismFor
ontolex-db-export -v bv -p noun

# <urn:uuid:5ede5896-67a0-4223-bb79-817c646cecd3> a lexinfo:initialism,
#        ontolex:LexicalEntry,
#        ontolex:Word ;
#    rdfs:label "bv"@nl ;
#    lexinfo:initialismFor <urn:uuid:5b4c4848-8ad7-429d-88c4-7eb223a5fb5b> ;
#    lexinfo:partOfSpeech lexinfo:noun .
```

## adding senses
Senses can be added to existing lexicalEntries. It is then possible to add a definition,
add references to external identifiers and add relations between them.
```bash
# add a sense to a lexicalEntry and look see the new lexicalSense
ontolex-db-manager add sense -s urn:uuid:8e1c3fc7-1b93-420f-88c5-568a15113536
ontolex-db-export -i urn:uuid:8e1c3fc7-1b93-420f-88c5-568a15113536

# now, add a relation between 2 senses
# in this case, a pertainsTo relation between adjective and noun
ontolex-db-manager add relation -s urn:uuid:02d56dfb-89de-4484-86db-d82feb132e64 -t urn:uuid:fa4f2e70-cfc9-4c4f-ba50-9c756da99d2b -r lexinfo:pertainsTo
ontolex-db-export -v conjunctureel -p adjective

# <urn:uuid:0a7756cc-a9b5-4adb-bab2-0d9d2a4f686c> a ontolex:LexicalEntry,
#         ontolex:Word ;
#     rdfs:label "conjunctureel"@nl ;
#     lexinfo:partOfSpeech lexinfo:adjective ;
#     ontolex:canonicalForm <urn:uuid:3dc209a2-a34e-45f8-9654-76e56ba35431> ;
#     ontolex:sense <urn:uuid:02d56dfb-89de-4484-86db-d82feb132e64> .
#
# <urn:uuid:02d56dfb-89de-4484-86db-d82feb132e64> a skos:Concept,
#         ontolex:LexicalSense ;
#     rdfs:label "conjunctureel"@nl ;
#     lexinfo:pertainsTo <urn:uuid:fa4f2e70-cfc9-4c4f-ba50-9c756da99d2b> .
#
# <urn:uuid:3dc209a2-a34e-45f8-9654-76e56ba35431> a ontolex:Form ;
#     ontolex:writtenRep "conjunctureel"@nl .
```

## Adding components
Components are usually initiated for a common subpart on the commandline, and used to start
gathering new components based on that first one. For example, the Dutch *aanhouden* can be
divided in *aan* and *houden*, similar to the English *deactivate*.
```bash
# get the lexicalFormID and add a component
ontolex-db-export -v aan -p adverb
ontolex-db-manager add component -s urn:uuid:63a6d052-3ee6-4cba-9c07-a66b01cf77a4

# stored component: urn:uuid:6adcd994-3e76-4dbb-ad91-000d6e31211a
# and refresh the export
ontolex-db-export --package --transitive > export.ttl

# now use that identifier in the verb-components ruleset
ontolex-db-ruleset --verb-components urn:uuid:6adcd994-3e76-4dbb-ad91-000d6e31211a
```
To manage these types of components, a quick overview of used components can be
retrieved with the ontolex-db-query function.
```bash
ontolex-db-query --verb-components-prefix
# +-----------------------------------------------+--------+-------+
# |                  componentID                  | label  | count |
# +-----------------------------------------------+--------+-------+
# | urn:uuid:b48de12d-ee93-46b1-b1c8-d55bbe92eeff |   op   |   76  |
# | urn:uuid:77a8b18d-7161-49eb-99bb-8647ebd80949 |  uit   |   65  |
# | urn:uuid:6adcd994-3e76-4dbb-ad91-000d6e31211a |  aan   |   63  |
# +-----------------------------------------------+--------+-------+
```
