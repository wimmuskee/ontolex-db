DROP TABLE IF EXISTS languageVocabulary;

CREATE TABLE languageVocabulary (
id TINYINT UNSIGNED NOT NULL PRIMARY KEY auto_increment,
iso_639_1 varchar(2) NOT NULL
);

INSERT INTO languageVocabulary (iso_639_1) VALUES ('nl');
INSERT INTO languageVocabulary (iso_639_1) VALUES ('en');
