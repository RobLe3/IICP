#!/usr/bin/env bash
# Run the current implementation-backed native framing fixture in each
# maintained SDK checkout. This is intentionally a local maintainer gate; each
# SDK CI runs its own copied fixture test independently.
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
workspace=$(cd "$root/.." && pwd)
rust="$workspace/iicp-client-rust"
python="$workspace/iicp-client-python"
typescript="$workspace/iicp-client-typescript"

for checkout in "$rust" "$python" "$typescript"; do
  [[ -d "$checkout" ]] || { echo "missing SDK checkout: $checkout" >&2; exit 2; }
done

python3 "$root/tools/check_native_framing_fixtures.py" \
  --copy "$rust/tests/fixtures/native-framing-v1.json" \
  --copy "$python/tests/fixtures/native-framing-v1.json" \
  --copy "$typescript/tests/fixtures/native-framing-v1.json"

(cd "$rust" && cargo test --test native_framing_fixture)
(cd "$python" && .venv/bin/python -m pytest -q tests/test_native_framing_fixture.py)
(cd "$typescript" && npx tsx --test tests/native_framing_fixture.test.ts)
