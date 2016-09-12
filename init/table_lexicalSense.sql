DROP TABLE IF EXISTS lexicalSense;

CREATE TABLE lexicalSense (
lexicalSenseID INT UNSIGNED NOT NULL PRIMARY KEY auto_increment,
lexicalEntryID INT UNSIGNED NOT NULL,
identifier VARCHAR(150) NOT NULL UNIQUE
);
