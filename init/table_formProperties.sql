DROP TABLE IF EXISTS formProperties;

CREATE TABLE formProperties (
lexicalFormID INT UNSIGNED NOT NULL,
propertyID TINYINT UNSIGNED NOT NULL
);

ALTER TABLE formProperties ADD INDEX i_formProperties_propertyID ( propertyID );
