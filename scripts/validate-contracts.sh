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

# Generated-Go gates: descriptor compilation alone lets gen/ drift silently.
# When buf, Go, and git are available, verify the committed generated code is
# both fresh (buf generate produces no diff) and compilable. The gates skip
# only when a tool is genuinely absent; a failing gate fails the script.
missing=()
command -v buf >/dev/null 2>&1 || missing+=(buf)
command -v go >/dev/null 2>&1 || missing+=(go)
command -v git >/dev/null 2>&1 || missing+=(git)

if [[ ${#missing[@]} -gt 0 ]]; then
  echo "Skipping generated-code gates; not installed: ${missing[*]}" >&2
  exit 0
fi

(cd "$repo_root" && buf generate)
if ! (cd "$repo_root" && git diff --exit-code -- gen/); then
  echo "Generated code is stale; run 'buf generate' and commit the result." >&2
  exit 1
fi
(cd "$repo_root/gen/go" && go mod download && go build ./...)
echo "Generated Go code is current and compiles."
