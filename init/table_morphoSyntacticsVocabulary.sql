DROP TABLE IF EXISTS morphoSyntacticsVocabulary;

CREATE TABLE morphoSyntacticsVocabulary (
id TINYINT UNSIGNED NOT NULL PRIMARY KEY auto_increment,
property ENUM('number','person','tense') NOT NULL,
value VARCHAR(30) NOT NULL
);

INSERT INTO morphoSyntacticsVocabulary (property,value) VALUES ('number','singular' );
INSERT INTO morphoSyntacticsVocabulary (property,value) VALUES ('number','plural' );
INSERT INTO morphoSyntacticsVocabulary (property,value) VALUES ('person','firstPerson');
INSERT INTO morphoSyntacticsVocabulary (property,value) VALUES ('person','secondPerson');
INSERT INTO morphoSyntacticsVocabulary (property,value) VALUES ('person','thirdPerson');
INSERT INTO morphoSyntacticsVocabulary (property,value) VALUES ('tense','present');
INSERT INTO morphoSyntacticsVocabulary (property,value) VALUES ('tense','past');
INSERT INTO morphoSyntacticsVocabulary (property,value) VALUES ('tense','future');