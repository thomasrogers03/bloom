#!/bin/bash

set -xeou pipefail

antlr4 -Dlanguage=Python3 -o bloom/parsers bloom/resources/parsers/Actor.g4
