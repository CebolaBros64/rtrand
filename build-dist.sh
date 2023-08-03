#!/bin/bash

rm -fr dist/
cxfreeze -c main.py --target-dir $1
cp -r resources $1/
