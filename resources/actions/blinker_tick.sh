#!/bin/bash

SOUND="$(dirname $(dirname $(realpath $0)))/Tick_$1.wav"

count=$(bc <<< "ibase=16; $(echo "$2" | tr a-z A-Z)")

for (( i=0; i<count; i++ ))
do

su -c "mpv $SOUND" pi &
sleep 1.601

done

exit 0