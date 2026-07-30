#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${1:-$ROOT/standards/ietf/draft-roble-iicp-peer.md}"
OUT="${2:-$ROOT/build/ietf}"

command -v kramdown-rfc >/dev/null 2>&1 || {
  echo "missing kramdown-rfc; install the pinned version from standards/ietf/Gemfile" >&2
  exit 2
}
command -v xml2rfc >/dev/null 2>&1 || {
  echo "missing xml2rfc; install version from standards/ietf/requirements.txt" >&2
  exit 2
}

mkdir -p "$OUT"
base="$(basename "$SOURCE" .md)"
xml="$OUT/$base.xml"

kramdown-rfc "$SOURCE" >"$xml"
xml2rfc --strict --text --html --path "$OUT" "$xml"

grep -q 'This document makes no IANA request' "$SOURCE"
! grep -Eiq '9484.{0,40}(assigned|reserved) (to|for) IICP' "$SOURCE"

echo "Internet-Draft build passed: $OUT"
