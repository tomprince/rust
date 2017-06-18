#!/bin/bash

set -e

mkdir -p "$HOME/rustsrc"


pwd

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
