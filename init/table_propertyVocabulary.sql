DROP TABLE IF EXISTS propertyVocabulary;

CREATE TABLE propertyVocabulary (
id TINYINT UNSIGNED NOT NULL PRIMARY KEY auto_increment,
property VARCHAR(150) NOT NULL,
value VARCHAR(150) NOT NULL
);

INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#number','http://www.lexinfo.net/ontology/2.0/lexinfo#singular' );
INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#number','http://www.lexinfo.net/ontology/2.0/lexinfo#plural' );
INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#person','http://www.lexinfo.net/ontology/2.0/lexinfo#firstPerson');
INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#person','http://www.lexinfo.net/ontology/2.0/lexinfo#secondPerson');
INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#person','http://www.lexinfo.net/ontology/2.0/lexinfo#thirdPerson');
INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#tense','http://www.lexinfo.net/ontology/2.0/lexinfo#present');
INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#tense','http://www.lexinfo.net/ontology/2.0/lexinfo#past');
INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#tense','http://www.lexinfo.net/ontology/2.0/lexinfo#future');
INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#degree','http://www.lexinfo.net/ontology/2.0/lexinfo#comparative');
INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#degree','http://www.lexinfo.net/ontology/2.0/lexinfo#superlative');
INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#gender','http://www.lexinfo.net/ontology/2.0/lexinfo#neuter');
INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#gender','http://www.lexinfo.net/ontology/2.0/lexinfo#feminine');
INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#gender','http://www.lexinfo.net/ontology/2.0/lexinfo#masculine');
INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#partOfSpeech','http://www.lexinfo.net/ontology/2.0/lexinfo#diminutiveNoun');
INSERT INTO propertyVocabulary (property,value) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#morphosyntacticProperty','http://www.isocat.org/datcat/DC-2207');
