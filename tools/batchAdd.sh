#!/bin/bash
# select random words from a provided wordlist, and
# add them as noun, adjective or verb


notfound=$1

if [ -z ${notfound} ]; then
	echo "error: no input terms provided"
	exit 1
fi

if [ ! -f ${notfound} ]; then
	echo "error: provided input terms do not exist: ${notfound}"
	exit 1
fi

for line in $(cat $notfound | sort -R); do
	echo $line
	read answer

	case ${answer} in
		"n") ../ontolex-db-manager -c ../config.json add entry -w ${line} -p noun ;;
		"a") ../ontolex-db-manager -c ../config.json add entry -w ${line} -p adjective ;;
		"v") ../ontolex-db-manager -c ../config.json add entry -w ${line} -p verb ;;
		*) echo "do nothing" ;;
	esac
done
