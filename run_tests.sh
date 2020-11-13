#!/bin/bash

set -eou pipefail

mkdir test_results
python -m unittest bloom.tests
