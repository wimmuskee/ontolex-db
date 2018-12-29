from database.mysql import Database


class Bulk(Database):
    def __init__(self,config,language):
        Database.__init__(self,config)
        self.connect()
        self.setLanguages()
        self.setPosses()
        self.setProperties()
        self.setEntryRelations()
        self.setSenseRelations()

        self.language_id = self.languages[language]
        self.keymap = {
            "ontolex:LexicalEntry": "",
            "lexinfo:partOfSpeech": "",
            "lexinfo:gender": "",
            "lexinfo:abbreviationFor": "",
            "lexinfo:initialismFor": "",
            "lexinfo:acronymFor": "",
            "lexinfo:hypernym": "",
            "ontolex:reference": "",
            "lexinfo:pertainsTo": "" }
        self.pos_id = None
        self.lexicalEntryID = None
        self.lexicalSenseID = None

    def setRow(self,row):
        """ Validates and sets keymap for provided row."""
        for key in self.keymap:
            self.keymap[key] = self.__validateRowInput(row,key)

        if not self.keymap["ontolex:LexicalEntry"] or not self.keymap["lexinfo:partOfSpeech"] :
            raise ValueError("error adding row: lexicalEntry and partOfSpeech are required")

        if self.keymap["lexinfo:partOfSpeech"] not in self.posses:
            raise ValueError("error adding row: invalid partOfSpeech: " + self.keymap["lexinfo:partOfSpeech"])

        self.pos_id = self.posses[self.keymap["lexinfo:partOfSpeech"]]
        self.lexicalEntryID = None
        self.lexicalSenseID = None

    def storeRow(self):
        self.__setLexicalEntryID()
        self.__setGender(self.keymap["lexinfo:gender"])
        self.__setContractions()

        # senses
        self.__setReference(self.keymap["ontolex:reference"])
        self.__setHypernym(self.keymap["lexinfo:hypernym"])
        self.__setPertainsTo(self.keymap["lexinfo:pertainsTo"])


    def __validateRowInput(self,rowdict,key):
        """ Simple validation for csv input. """
        if key in rowdict and rowdict[key]:
            return rowdict[key].strip(' \t\n\r')
        else:
            return ""

    def __setLexicalEntryID(self):
        self.lexicalEntryID = self.findLexicalEntry(self.keymap["ontolex:LexicalEntry"],self.pos_id)
        if not self.lexicalEntryID:
            self.lexicalEntryID = self.storeCanonical(self.keymap["ontolex:LexicalEntry"],self.language_id,self.pos_id)

    def __setGender(self,gender):
        """ Only add gender to canonicalForm of provided lexicalEntry."""
        if "gender:" + gender not in self.properties:
            return

        lexicalFormID = self.findlexicalForm(self.lexicalEntryID,self.keymap["ontolex:LexicalEntry"],self.language_id)

        # check if property exists already
        if lexicalFormID:
            self.insertFormProperty(lexicalFormID,self.properties["gender:" + gender],True)


    def __setContractions(self):
        contraction_types = ["lexinfo:abbreviationFor","lexinfo:initialismFor","lexinfo:acronymFor"]
        contraction_entry = ""

        # pick one of them, last one wins
        for ctype in contraction_types:
            if self.keymap[ctype]:
                contraction_entry = self.keymap[ctype]
                contraction_rel = ctype

        # and store and set relation to entry
        if contraction_entry:
            contractionLexID = self.findLexicalEntry(contraction_entry,self.pos_id)
            if not contractionLexID:
                contractionLexID = self.storeCanonical(contraction_entry,self.language_id,self.pos_id)
            contractionIdentifier = self.getIdentifier(contractionLexID,"lexicalEntry")
            self.storeLexicalEntryRelation(self.lexicalEntryID,self.entryrelations[contraction_rel],contractionIdentifier)

    def __setReference(self,reference):
        if not reference:
            return

        if self.lexicalSenseID:
            # if a senseID is set locally, we're gonna assume all columns are for the same sense
            self.insertSenseReference(self.lexicalSenseID,"ontolex:reference",reference)
        else:
            self.lexicalSenseID = self.storeLexicalSense(self.lexicalEntryID,"ontolex:reference",reference)
            if not self.lexicalSenseID:
                self.__printWarning(self.keymap["ontolex:LexicalEntry"])

    def __setHypernym(self,hypernym):
        if not hypernym:
            return

        if self.lexicalSenseID:
            # if a senseID is set locally, we're gonna assume all columns are for the same sense
            self.insertSenseReference(self.lexicalSenseID,"lexinfo:hypernym",hypernym)
        else:
            self.lexicalSenseID = self.storeLexicalSense(self.lexicalEntryID,"lexinfo:hypernym",hypernym)
            if not self.lexicalSenseID:
                self.__printWarning(self.keymap["ontolex:LexicalEntry"])

    def __setPertainsTo(self,pertainsto):
        if not pertainsto:
            return

        adjectiveID = self.findLexicalEntry(pertainsto,self.posses["adjective"])
        if not adjectiveID:
            adjectiveID = self.storeCanonical(pertainsto,self.language_id,db.posses["adjective"])

        # we need lexicalSenses for the entry and the adjective
        # check if exists from another column, and check again if adding new
        if not self.lexicalSenseID:
            senseCount = self.getCountlexicalSenses(self.lexicalEntryID)
            if senseCount == 0:
                self.lexicalSenseID = self.insertLexicalSense(self.lexicalEntryID)
            elif senseCount == 1:
                self.lexicalSenseID = self.getLexicalSenseID(self.lexicalEntryID)
            else:
                self.__printWarning(self.keymap["ontolex:LexicalEntry"])

        lexicalSenseIdentifier = self.getIdentifier(self.lexicalSenseID,"lexicalSense")
        adjectiveSenseID = self.storeLexicalSense(adjectiveID,"lexinfo:pertainsTo",lexicalSenseIdentifier)
        if not adjectiveSenseID:
            self.__printWarning(pertainsto)

    def __printWarning(self,value):
        print("error adding sense data: probably multiple senses for: " + value)
