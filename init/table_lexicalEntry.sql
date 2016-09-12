DROP TABLE IF EXISTS lexicalEntry;

CREATE TABLE lexicalEntry (
lexicalEntryID INT UNSIGNED NOT NULL PRIMARY KEY auto_increment,
identifier VARCHAR(150) NOT NULL UNIQUE,
value VARCHAR(255) NOT NULL,
class ENUM('Word','MultiwordExpression','Affix') NOT NULL DEFAULT 'Word',
partOfSpeechID TINYINT NULL
);
