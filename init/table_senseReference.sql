DROP TABLE IF EXISTS senseReference;

CREATE TABLE senseReference (
lexicalSenseID INT UNSIGNED NOT NULL,
namespace ENUM('ontolex','skos', 'skos-thes') NOT NULL,
property ENUM('reference','broader','related','exactMatch', 'broaderInstantial', 'broaderPartitive') NOT NULL,
reference VARCHAR(150) NOT NULL
);
