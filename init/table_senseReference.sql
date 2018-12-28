DROP TABLE IF EXISTS senseReference;

CREATE TABLE senseReference (
lexicalSenseID INT UNSIGNED NOT NULL,
namespace ENUM('ontolex','lexinfo') NOT NULL,
property ENUM('reference','synonym','antonym','pertainsTo','relatedTerm','hypernym') NOT NULL,
reference VARCHAR(150) NOT NULL
);

ALTER TABLE senseReference ADD INDEX i_senseReference_lexicalSenseID ( lexicalSenseID );
ALTER TABLE senseReference ADD UNIQUE i_senseReference_unique ( lexicalSenseID, namespace, property, reference );
