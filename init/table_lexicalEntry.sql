DROP TABLE IF EXISTS lexicalEntry;

CREATE TABLE lexicalEntry (
lexicalEntryID INT UNSIGNED NOT NULL PRIMARY KEY auto_increment,
value VARCHAR(255) NOT NULL,
class ENUM('Word','MultiwordExpression','Affix') NOT NULL DEFAULT 'Word',
partOfSpeechID TINYINT NULL
);

ALTER TABLE lexicalEntry ADD UNIQUE u_lexicalEntry_value_partOfSpeechID ( value, partOfSpeechID );
