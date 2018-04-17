#!/bin/bash
# select all alphanumeric single words from a file and
# compare them to the file with all forms. 
# output all words that have not been found

inputterms=$1

if [ -z ${inputterms} ]; then
	echo "error: no input terms provided"
	exit 1
fi

if [ ! -f ${inputterms} ]; then
	echo "error: provided input terms do not exist: ${inputterms}"
	exit 1
fi

termsUniqAZ=$(mktemp)
cat ${inputterms} | sort | uniq | grep "^[a-z]*$" > ${termsUniqAZ}


for line in $(cat ${termsUniqAZ}); do
	if [[ "$(cat forms.txt | grep $line)" == "" ]]; then
		echo $line
	fi
done

rm ${termsUniqAZ}
