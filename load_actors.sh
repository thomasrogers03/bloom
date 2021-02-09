#!/bin/bash

set -eou pipefail

if [ "$#" -ne 1 ]; then
    echo Need path to kpf file
    exit 1
fi

kpf_path=$1
rm -rf kpf
unzip -q "$kpf_path" -d kpf

python load_actors.py
