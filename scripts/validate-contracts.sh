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

# Well-known types (google/protobuf/*.proto): prefer the system include path;
# fall back to PROTOC_WKT_INCLUDE when the compiler ships its own includes
# (for example a release-archive protoc on a machine without protobuf-compiler).
wkt_include=/usr/include
if [[ ! -f /usr/include/google/protobuf/timestamp.proto ]]; then
  : "${PROTOC_WKT_INCLUDE:?/usr/include lacks protobuf well-known types; set PROTOC_WKT_INCLUDE to a directory containing google/protobuf/*.proto}"
  wkt_include="$PROTOC_WKT_INCLUDE"
fi

protoc \
  -I "$repo_root/proto" \
  -I "$wkt_include" \
  --descriptor_set_out="$out" \
  --include_imports \
  "${proto_files[@]}"

test -s "$out"
echo "Validated ${#proto_files[@]} contract files into a Protocol Buffers descriptor set."
