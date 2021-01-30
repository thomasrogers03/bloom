#!/bin/bash

set -eou pipefail

if [ "$#" -ne 1 ]; then
    echo Need path to kpx file
    exit 1
fi

kpx_path=$1
rm -rf kpx
unzip -q $kpx_path -d kpx

python load_actors.py
