DROP TABLE IF EXISTS lexicalEntryRelation;

CREATE TABLE lexicalEntryRelation (
lexicalEntryID INT UNSIGNED NOT NULL,
relationID TINYINT UNSIGNED NOT NULL,
reference VARCHAR(150) NOT NULL
);

ALTER TABLE lexicalEntryRelation ADD INDEX i_lexicalEntryRelation_lexicalEntryID ( lexicalEntryID );
ALTER TABLE lexicalEntryRelation ADD INDEX i_lexicalEntryRelation_relationID ( relationID );
