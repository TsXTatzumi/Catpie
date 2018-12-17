#!/bin/bash

LAST_CATPIE_COMMAND="Last NYAN"
CONFIG_CATPIE="$(dirname $(dirname $(realpath $0)))/Catpie.cfg"


if [ $# -lt 1 ]; then
printf "pattern: schaltung.sh <signal> [count] \nsignal:\n	up\n	down\n	mode\ncount is a number\n"
exit -1
fi


OIFS=$IFS; IFS='\n'

while read -r line || [[ -n "$line" ]]; do

regex="^$LAST_CATPIE_COMMAND	"
if [[ $line =~ $regex ]]; then
last=$line
fi

done < "$CONFIG_CATPIE"

IFS=$OIFS


if [ $1 = "up" ]; then
signal=21

elif [ $1 = "down" ]; then
signal=20

elif [ $1 = "mode" ]; then
signal=16

else
printf "invalid signal\nsignal:\n	up\n	down\n	mode\n"
exit -1
fi


if ! [[ $2 =~ '^[0-9]+$' ]]; then
count=$2

else
printf "count is a number\n"
exit -1
fi

if [[ $# -lt 2 ]]; then
count=1

fi


pigs modes $signal w

for (( i=0; i<count; i++ ))
do

pigs w $signal 1
sleep .2

pigs w $signal 0
sleep .2

done


OIFS=$IFS; IFS=''

if [ -n "$last" ]; then
sed -i 's/'"$last"'/'"$LAST_CATPIE_COMMAND	SCHALT $signal $count"'/' "$CONFIG_CATPIE"
else
printf "\n$LAST_CATPIE_COMMAND	SCHALT $signal $count" >> $CONFIG_CATPIE
fi

IFS=$OIFS

exit 0