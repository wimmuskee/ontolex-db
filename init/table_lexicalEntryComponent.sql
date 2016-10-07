DROP TABLE IF EXISTS lexicalEntryComponent;

CREATE TABLE lexicalEntryComponent (
lexicalEntryID INT UNSIGNED NOT NULL,
componentID INT UNSIGNED NOT NULL,
position TINYINT UNSIGNED NOT NULL
);

ALTER TABLE lexicalEntryComponent ADD INDEX i_lexicalEntryComponent_lexicalEntryID ( lexicalEntryID );
ALTER TABLE lexicalEntryComponent ADD INDEX i_lexicalEntryComponent_componentID ( componentID );
