DROP TABLE IF EXISTS writtenRep;

CREATE TABLE writtenRep (
lexicalFormID INT UNSIGNED NOT NULL,
languageID TINYINT UNSIGNED NOT NULL,
syllableCount TINYINT UNSIGNED NULL,
value VARCHAR(255) NOT NULL
);

ALTER TABLE writtenRep ADD INDEX i_writtenRep_lexicalFormID ( lexicalFormID );
