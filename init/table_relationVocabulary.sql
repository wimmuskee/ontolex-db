DROP TABLE IF EXISTS relationVocabulary;

CREATE TABLE relationVocabulary (
relationID TINYINT UNSIGNED NOT NULL PRIMARY KEY auto_increment,
relation VARCHAR(150) NOT NULL,
field ENUM('lexicalEntry','lexicalSense') NOT NULL
);

INSERT INTO relationVocabulary (relation,field) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#abbreviationFor','lexicalEntry');
INSERT INTO relationVocabulary (relation,field) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#initialismFor','lexicalEntry');
INSERT INTO relationVocabulary (relation,field) VALUES ('http://www.lexinfo.net/ontology/2.0/lexinfo#acronymFor','lexicalEntry');
