#!/bin/bash

set -xeou pipefail

cd bloom/resources/parsers
antlr4 -Dlanguage=Python3 -o ../../parsers Actor.g4
