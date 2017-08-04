DROP TABLE IF EXISTS senseReference;

CREATE TABLE senseReference (
lexicalSenseID INT UNSIGNED NOT NULL,
namespace ENUM('ontolex','skos', 'skos-thes','lexinfo') NOT NULL,
property ENUM('reference','broader','synonym','broaderInstantial','broaderPartitive','antonym','pertainsTo','relatedTerm','hypernym') NOT NULL,
reference VARCHAR(150) NOT NULL
);

ALTER TABLE senseReference ADD INDEX i_senseReference_lexicalSenseID ( lexicalSenseID );
