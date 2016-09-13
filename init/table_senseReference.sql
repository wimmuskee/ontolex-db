DROP TABLE IF EXISTS senseReference;

CREATE TABLE senseReference (
lexicalSenseID INT UNSIGNED NOT NULL,
namespace ENUM('ontolex','skos') NOT NULL,
property ENUM('reference','evokes','broader','related','exactMatch') NOT NULL,
reference VARCHAR(150) NOT NULL
);
