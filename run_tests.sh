#!/bin/bash

set -eou pipefail

mkdir -p test_results
rm -rf test_results/*
python -m unittest "$*"
