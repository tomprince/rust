#!/bin/bash

set -e

mkdir -p "$HOME/rustsrc"
curl -o "$HOME/stamp" https://s3.amazonaws.com/rust-lang-ci/rust-ci-mirror/2017-03-17-stamp-x86_64-unknown-linux-musl
chmod +x "$HOME/stamp"
export PATH=$PATH:$HOME

echo
echo
echo "#### Disk usage before running script:";
df -h;
du . | sort -nr | head -n100

RUN_SCRIPT="stamp src/ci/init_repo.sh . $HOME/rustsrc";
export RUN_SCRIPT="$RUN_SCRIPT && stamp src/ci/docker/run.sh $IMAGE";
sh -x -c "$RUN_SCRIPT"

echo
echo
echo "#### Build finished; Disk usage after running script:";
df -h;
du . | sort -nr | head -n100
