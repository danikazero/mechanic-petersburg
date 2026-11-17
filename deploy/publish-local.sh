#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ $# -ne 1 || ! "$1" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]]; then
    echo 'Usage: deploy/publish-local.sh RELEASE_ID' >&2
    exit 2
fi
release="releases/$1"
for file in index.html index.js index.wasm index.pck; do
    test -s "public/$release/$file"
done
switch="$(mktemp -d public/.publish.XXXXXX)"
trap 'rm -f -- "$switch/current"; rmdir -- "$switch"' EXIT
ln -s -- "$release" "$switch/current"
mv -Tf -- "$switch/current" public/current
