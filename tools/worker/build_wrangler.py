"""Write wrangler.toml with the door's guest list copied in, so the Worker
admits exactly the names the site admits. Run after any change to gate.js:

    python3 tools/worker/build_wrangler.py
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
gate = (HERE.parent.parent / "assets" / "gate.js").read_text()
block = gate[gate.index("var HASHES = {"):]
block = block[:block.index("};")]
hashes = re.findall(r'"([0-9a-f]{64})": 1', block)
assert len(hashes) >= 30, len(hashes)

toml = f'''name = "ca-photographs"
main = "photographs.js"
compatibility_date = "2026-08-01"

[[r2_buckets]]
binding = "PHOTOS"
bucket_name = "ca-photographs"
jurisdiction = "eu"

[vars]
ALLOWED_ORIGIN = "https://coleswedding.com"
# uploads close at the end of this day (UTC); change and redeploy to extend
CLOSES = "2026-12-31T23:59:59Z"
# the door's guest list, generated from assets/gate.js; never edit by hand
HASHES = "{",".join(hashes)}"
'''
(HERE / "wrangler.toml").write_text(toml)
print(f"wrangler.toml written with {len(hashes)} fingerprints")
