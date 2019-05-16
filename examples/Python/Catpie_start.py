#!/usr/bin/env python

from Catpie import Cat
import sys

if len(sys.argv) >= 2:
    state = sys.argv[1]
    
    if state == "eat" or state == "bake":
        Cat.pie(state)
    else:
        print("Usage: python start.py [eat|bake]")
        sys.exit(-1)
else:
    Cat.pie ("eat")