#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="$(mktemp)"
trap 'rm -f "$out"' EXIT

mapfile -t proto_files < <(find "$repo_root/proto" -name '*.proto' -type f | sort)
if [[ ${#proto_files[@]} -eq 0 ]]; then
  echo "No Protocol Buffers files found" >&2
  exit 1
fi

protoc \
  -I "$repo_root/proto" \
  -I /usr/include \
  --descriptor_set_out="$out" \
  --include_imports \
  "${proto_files[@]}"

test -s "$out"
echo "Validated ${#proto_files[@]} contract files into a Protocol Buffers descriptor set."
