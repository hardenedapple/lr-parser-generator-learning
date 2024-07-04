#!/bin/bash
for i in *.py; do
    echo -n '' | python3 $i
done
