#!/bin/bash

LAST_CATPIE_COMMAND="Last NYAN"
MODULES_DIR=$(dirname $(realpath $0))
CONFIG_CATPIE="$(dirname $MODULES_DIR)/Catpie.cfg"


OIFS=$IFS; IFS='\n'

while read -r line || [[ -n "$line" ]]; do

regex="^$LAST_CATPIE_COMMAND	"
if [[ $line =~ $regex ]]; then
last=$line
fi

done < "$CONFIG_CATPIE"

IFS=$OIFS


OIFS=$IFS; IFS='	'

if [ -n "$last" ]; then

read -r -a lastarr <<< "$last"

IFS=' '

read -r -a lastarr <<< "${lastarr[1]}"

if [ "${lastarr[0]}" = "BLINK" ]; then
bash $MODULES_DIR/blinker.sh fancy left 0

elif [ "${lastarr[0]}" = "SCHALT" ]; then
if [ "${lastarr[1]}" = "up" ]; then
bash $MODULES_DIR/schaltung.sh down ${lastarr[2]}

elif [ "${lastarr[1]}" = "down" ]; then
bash $MODULES_DIR/schaltung.sh up ${lastarr[2]}

elif [ "${lastarr[1]}" = "mode" ]; then
n=3-${lastarr[2]}%3
bash $MODULES_DIR/schaltung.sh mode $n

fi
fi
fi

IFS=$OIFS


OIFS=$IFS; IFS=''

if [ -n "$last" ]; then
sed -i 's/'"$last"'/'"$LAST_CATPIE_COMMAND	NAYN"'/' "$CONFIG_CATPIE"
else
printf "\n$LAST_CATPIE_COMMAND	NAYN" >> $CONFIG_CATPIE
fi

IFS=$OIFS

exit 0