#!/bin/bash

set -eou pipefail

rm -rf dist/*

python setup.py bdist_apps
python setup.py bdist_wheel

./run_tests.sh bloom.tests
