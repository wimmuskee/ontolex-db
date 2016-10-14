DROP TABLE IF EXISTS partOfSpeechVocabulary;

CREATE TABLE partOfSpeechVocabulary (
id TINYINT UNSIGNED NOT NULL PRIMARY KEY auto_increment,
value VARCHAR(50) NOT NULL
);

INSERT INTO partOfSpeechVocabulary (value) VALUES ('noun');
INSERT INTO partOfSpeechVocabulary (value) VALUES ('verb');
INSERT INTO partOfSpeechVocabulary (value) VALUES ('adjective');
INSERT INTO partOfSpeechVocabulary (value) VALUES ('adverb');
INSERT INTO partOfSpeechVocabulary (value) VALUES ('article');
INSERT INTO partOfSpeechVocabulary (value) VALUES ('conjunction');
INSERT INTO partOfSpeechVocabulary (value) VALUES ('preposition');
INSERT INTO partOfSpeechVocabulary (value) VALUES ('pronoun');
INSERT INTO partOfSpeechVocabulary (value) VALUES ('numeral');
INSERT INTO partOfSpeechVocabulary (value) VALUES ('cardinalNumeral');
INSERT INTO partOfSpeechVocabulary (value) VALUES ('interjection');
INSERT INTO partOfSpeechVocabulary (value) VALUES ('pastParticipleAdjective');
INSERT INTO partOfSpeechVocabulary (value) VALUES ('presentParticipleAdjective');
