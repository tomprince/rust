#!/bin/bash

set -e

mkdir -p "$HOME/rustsrc"

echo
echo
echo "#### Disk usage before running script:";
df -h;
du . | sort -nr | head -n100

src/ci/init_repo.sh . "$HOME/rustsrc"

if grep -q "FROM rust-ci-base" "src/ci/docker/$IMAGE/Dockerfile"; then
    docker \
      build \
      --rm \
      -t rust-ci-base \
      -f "src/ci/docker/base/Dockerfile" \
      "src/ci/docker"
fi

docker \
    build \
    --rm \
    -t rust-ci \
    -f "src/ci/docker/$IMAGE/Dockerfile" \
    "src/ci/docker"

docker \
    save \
    -o "image.tar" \
    rust-ci

echo
echo
echo "#### Build finished; Disk usage after running script:";
df -h;
du . | sort -nr | head -n100
