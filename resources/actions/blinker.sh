#!/bin/bash

BT_NAME="BlingHelmet 60"
LAST_CATPIE_COMMAND="Last NYAN"
MODULES_DIR=$(dirname $(realpath $0))
CONFIG_CATPIE="$(dirname $MODULES_DIR)/Catpie.cfg"


if [ $# -lt 3 ]; then
printf "pattern: blinker.sh <mode> <direction> <cycles> \nmodes:\n	fancy\n	lame\ndirections:\n	left\n	right\n cycles in hex (0xff) or decimal (255)\n"
exit -1
fi


OIFS=$IFS; IFS='\n'

while read -r line || [[ -n "$line" ]]; do

regex="^$BT_NAME	"
if [[ $line =~ $regex ]]; then
option=$line
fi

regex="^$LAST_CATPIE_COMMAND	"
if [[ $line =~ $regex ]]; then
last=$line
fi

done < "$CONFIG_CATPIE"

IFS=$OIFS


OIFS=$IFS; IFS='	'

read -r -a option <<< $option
mac=${option[1]//:/_}

IFS=$OIFS


if [ -z "$mac" ]; then
printf "no $BT_NAME connected"
exit -1
fi


if [ $1 = "fancy" ]; then
mode=0x02

elif [ $1 = "lame" ]; then
mode=0x04

else
printf "invalid mode\nmodes:\n	fancy\n	lame\n"
exit -1
fi


if [ $2 = "right" ]; then
(( mode++ ))

elif [ $2 != "left" ]; then
printf "invalid direction\ndirections:\n	left\n	right\n"
exit -1
fi


if ! [[ $3 =~ '^[0-9]+$' ]]; then
if [ $3 -lt 256 ]; then
cycles="0"$(bc <<< "obase=16; $3")
cycles="0x"${cycles[@]: -2}
else
printf "invalid number of cycles\n cycles in hex (0xff) or decimal (255)\n"
exit -1
fi

elif ! [[ $3 =~ '^0x([0-9A-Fa-f]{2})$' ]] ; then
cycles=$3

else
printf "invalid number of cycles\n cycles in hex (0xff) or decimal (255)\n"
exit -1
fi


sudo systemctl start bluetooth
echo -e "select-attribute /org/bluez/hci0/dev_$mac/service0009/char000a\nwrite 0x55 0xaa 0x10 0x02 0x01 $mode $cycles 0x02\nexit" | bluetoothctl


OIFS=$IFS; IFS=''

if [ -n "$last" ]; then
sed -i 's/'"$last"'/'"$LAST_CATPIE_COMMAND	BLINK"'/' "$CONFIG_CATPIE"
else
printf "\n$LAST_CATPIE_COMMAND	BLINK" >> $CONFIG_CATPIE
fi

IFS=$OIFS

exit 0