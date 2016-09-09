DROP TABLE IF EXISTS lexicalForm;

CREATE TABLE lexicalForm (
lexicalFormID INT UNSIGNED NOT NULL PRIMARY KEY auto_increment,
lexicalEntryID INT UNSIGNED NOT NULL,
type ENUM('canonicalForm','otherForm') NOT NULL DEFAULT 'canonicalForm'
);
