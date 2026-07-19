#!/usr/bin/env python3
"""Apply a display order to the inspiration galleries.

Usage: python3 tools/apply_photo_order.py 5,1,12,3,...
The numbers are dress-NN photo numbers from tools/arrange.html, in the
desired display order. Rewrites the figure lists in index.html and
inspiration.html from tools/photos.json; photo files are not touched.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
manifest = {m["file"]: m for m in json.load(open(ROOT / "tools/photos.json"))}

order = [s.strip() for s in sys.argv[1].replace("photo order:", "").split(",") if s.strip()]
files = [f"dress-{int(n):02d}.jpg" for n in order]
missing = [f for f in files if f not in manifest]
assert not missing, f"unknown photos: {missing}"
assert len(files) == len(manifest), f"order lists {len(files)} of {len(manifest)} photos"

def figures(indent):
    return "\n".join(
        f'{indent}<figure><img src="/assets/img/dress/{f}" alt="{manifest[f]["alt"]}" loading="lazy" '
        f'width="{manifest[f]["w"]}" height="{manifest[f]["h"]}"></figure>'
        for f in files)

for name, indent in [("index.html", "            "), ("inspiration.html", "  ")]:
    p = ROOT / name
    t = p.read_text()
    start = t.index('<div class="dress-photos">')
    # the gallery contains only <figure><img></figure> lines, so the first
    # closing div after its opening tag is its own close
    end = t.index("</div>", start) + len("</div>")
    close_indent = "          " if name == "index.html" else "  "
    t = t[:start] + '<div class="dress-photos">\n' + figures(indent) + f"\n{close_indent}</div>" + t[end:]
    p.write_text(t)
    print(f"{name}: reordered")
print("done; commit and push to deploy")
