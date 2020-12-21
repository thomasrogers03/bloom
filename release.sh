#!/bin/bash

set -eou pipefail

version=$(cat version.txt)
branch=$(git rev-parse --abbrev-ref HEAD)
sha=$(git rev-parse HEAD)

echo "Creating release $branch-$version"
echo ghr -t $GITHUB_TOKEN -u thomasrogers03 -r bloom -c $sha -draft -replace "$branch-$version" ./dist/
