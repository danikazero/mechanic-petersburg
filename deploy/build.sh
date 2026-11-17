#!/usr/bin/env bash
set -euo pipefail
project="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# -ne 1 || -z "$1" || -L "$1" ]]; then
    echo 'Usage: deploy/build.sh NEW_OUTPUT_DIRECTORY' >&2
    exit 2
fi
out="$(realpath -m -- "$1")"
if [[ "$out" == "$project" || "$out" == "$project/"* ]]; then
    echo 'Choose an output directory outside the Godot project.' >&2
    exit 2
fi
mkdir -- "$out"
log="$out/build.log"
trap 'status=$?; if (( status != 0 )); then echo "Build failed. See $log" >&2; fi' EXIT
engine="${GODOT_BIN:-godot}"
"$engine" --headless --path "$project" --editor --import >"$log" 2>&1
"$engine" --headless --path "$project" --export-release Web "$out/index.html" >>"$log" 2>&1
for file in index.html index.js index.wasm index.pck; do
    test -s "$out/$file"
done
rm -- "$log"
echo "$out"
