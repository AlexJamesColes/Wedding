#!/usr/bin/env python3
"""Build the themed venues map for index.html from real geography.

Data: OpenStreetMap via Overpass (roads, parks, water) and OSRM (cab route),
cached in tools/geodata/. Projection is equal-scale equirectangular over
bbox lon -0.195..-0.062, lat 51.494..51.536 onto a 900x457 viewBox.

Elegance rules encoded here:
- roads stitched into chains; short slivers dropped; three ink weights
- speck polygons pruned (parks > 700 px^2, water > 90 px^2)
- route endpoints truncated to the venue markers (kills one-way loops)
- every label gets a "clearing": roads and route are masked out beneath
  label boxes, so no line threads between letterspaced characters
"""
import json, math, pathlib, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
GEO = pathlib.Path(__file__).resolve().parent / "geodata"
GEO.mkdir(exist_ok=True)

LON0, LON1, LAT0, LAT1 = -0.195, -0.062, 51.494, 51.536
W = 900
H = W * ((LAT1 - LAT0) / ((LON1 - LON0) * math.cos(math.radians(51.515))))
BBOX = f"{LAT0},{LON0},{LAT1},{LON1}"
UA = "coleswedding-map-build/1.0 (personal wedding site)"

TOWN_HALL = (-0.1631, 51.5225)
THE_NED = (-0.0894, 51.5134)


def fetch(name, url, data=None):
    f = GEO / name
    if f.exists():
        return json.load(open(f))
    req = urllib.request.Request(url, data=data.encode() if data else None,
                                 headers={"User-Agent": UA})
    body = urllib.request.urlopen(req, timeout=120).read()
    f.write_bytes(body)
    return json.loads(body)


def P(lon, lat):
    return ((lon - LON0) / (LON1 - LON0) * W, (LAT1 - lat) / (LAT1 - LAT0) * H)


def dp(pts, tol):
    if len(pts) < 3:
        return pts
    def perp(p, a, b):
        ax, ay = a; bx, by = b; px, py = p
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        d = perp(pts[i], pts[0], pts[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > tol:
        return dp(pts[:idx + 1], tol)[:-1] + dp(pts[idx:], tol)
    return [pts[0], pts[-1]]


def key(pt):
    return (round(pt[0], 1), round(pt[1], 1))


def stitch_chains(lines):
    lines = [list(l) for l in lines]
    used = [False] * len(lines)
    by_end = {}
    for i, l in enumerate(lines):
        by_end.setdefault(key(l[0]), []).append(i)
        by_end.setdefault(key(l[-1]), []).append(i)
    chains = []
    for i, l in enumerate(lines):
        if used[i]:
            continue
        used[i] = True
        chain = list(l)
        grew = True
        while grew:
            grew = False
            for endpt, reverse in [(chain[-1], False), (chain[0], True)]:
                for j in by_end.get(key(endpt), []):
                    if used[j]:
                        continue
                    seg = lines[j]
                    if key(seg[0]) == key(endpt):
                        add = seg[1:]
                    elif key(seg[-1]) == key(endpt):
                        add = list(reversed(seg))[1:]
                    else:
                        continue
                    used[j] = True
                    chain = (list(reversed(add)) + chain) if reverse else (chain + add)
                    grew = True
                    break
                if grew:
                    break
        chains.append(chain)
    return chains


def length(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def path_d(pts, close=False):
    return "M" + " L".join(f"{x:.0f},{y:.0f}" for x, y in pts) + (" Z" if close else "")


def ring_area(pts):
    n = len(pts)
    return abs(sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
                   for i in range(n))) / 2


# ── fetch ───────────────────────────────────────────────────────────
roads_q = ('[out:json][timeout:90];(way["highway"~"^(trunk|primary|secondary)$"]'
           f'({BBOX}););out geom;')
gw_q = ('[out:json][timeout:90];('
        f'way["leisure"="park"]({BBOX});relation["leisure"="park"]({BBOX});'
        f'way["natural"="water"]({BBOX});way["waterway"="river"]({BBOX});'
        ');out geom;')
roads_json = fetch("roads.json", "https://overpass-api.de/api/interpreter",
                   "data=" + urllib.parse.quote(roads_q))
gw_json = fetch("green-water.json", "https://overpass-api.de/api/interpreter",
                "data=" + urllib.parse.quote(gw_q))
route_json = fetch("route.json",
                   f"https://router.project-osrm.org/route/v1/driving/"
                   f"{TOWN_HALL[0]},{TOWN_HALL[1]};{THE_NED[0]},{THE_NED[1]}"
                   f"?overview=full&geometries=geojson")

# ── roads ───────────────────────────────────────────────────────────
raw = {"trunk": [], "primary": [], "secondary": []}
for wy in roads_json["elements"]:
    hw = wy.get("tags", {}).get("highway")
    if hw in raw and "geometry" in wy:
        raw[hw].append([P(g["lon"], g["lat"]) for g in wy["geometry"]])
buckets = {}
MIN_LEN = {"trunk": 20, "primary": 22, "secondary": 34}
for cls, lines in raw.items():
    chains = [dp(c, 2.4) for c in stitch_chains(lines)]
    buckets[cls] = [c for c in chains if length(c) > MIN_LEN[cls]]

# ── parks / lakes / thames ─────────────────────────────────────────
parks, lakes, thames_raw = [], [], []

def stitch_rel(members):
    segs = [[(g["lon"], g["lat"]) for g in m["geometry"]]
            for m in members if m.get("role") == "outer" and "geometry" in m]
    if not segs:
        return []
    rings, cur = [], segs.pop(0)
    while segs:
        for i, s in enumerate(segs):
            if s[0] == cur[-1]:
                cur += s[1:]; segs.pop(i); break
            if s[-1] == cur[-1]:
                cur += list(reversed(s))[1:]; segs.pop(i); break
        else:
            rings.append(cur); cur = segs.pop(0)
    rings.append(cur)
    return rings

for e in gw_json["elements"]:
    tags = e.get("tags", {})
    if e["type"] == "way" and "geometry" in e:
        pts = [P(g["lon"], g["lat"]) for g in e["geometry"]]
        closed = e["geometry"][0] == e["geometry"][-1]
        if tags.get("leisure") == "park" and closed:
            simp = dp(pts, 1.5)
            if ring_area(simp) > 700:
                parks.append(simp)
        elif tags.get("natural") == "water" and closed:
            simp = dp(pts, 1.2)
            if ring_area(simp) > 90:
                lakes.append(simp)
        elif tags.get("waterway") == "river" and "thames" in tags.get("name", "").lower():
            thames_raw.append(pts)
    elif e["type"] == "relation" and tags.get("leisure") == "park" and "members" in e:
        for ring in stitch_rel(e["members"]):
            pts = dp([P(lon, lat) for lon, lat in ring], 1.5)
            if len(pts) > 3 and ring_area(pts) > 700:
                parks.append(pts)

thames = max((dp(c, 0.8) for c in stitch_chains(thames_raw)), key=length)
if thames[0][0] > thames[-1][0]:
    thames.reverse()

# ── route, truncated to the markers ────────────────────────────────
MARK_A, MARK_B = P(*TOWN_HALL), P(*THE_NED)
route = dp([P(lon, lat) for lon, lat in
            route_json["routes"][0]["geometry"]["coordinates"]], 1.8)
i0 = max(i for i, p in enumerate(route) if math.dist(p, MARK_A) < 11)
i1 = min(i for i, p in enumerate(route) if math.dist(p, MARK_B) < 11)
route = route[i0:i1 + 1]

total = length(route)
acc, cab_pt = 0, route[0]
for i in range(len(route) - 1):
    seg = math.dist(route[i], route[i + 1])
    if acc + seg >= total * 0.40:
        t = (total * 0.40 - acc) / seg
        cab_pt = (route[i][0] + t * (route[i + 1][0] - route[i][0]),
                  route[i][1] + t * (route[i + 1][1] - route[i][1]))
        break
    acc += seg
cab_x, cab_y = round(cab_pt[0]), round(cab_pt[1])

# ── labels + clearings ─────────────────────────────────────────────
# (text, x, y_baseline, kind) — kinds set font/size; clearing boxes derive
# from estimated tracked width. rot rotates both text and clearing.
SC_D, IT = "sc-district", "italic"
LABELS = [
    ("Regent's Park", 270, 70, SC_D, 0, False),
    ("Hyde Park", 150, 305, SC_D, 0, False),
    ("Marylebone", 185, 212, SC_D, 0, True),
    ("Mayfair", 330, 318, SC_D, 0, True),
    ("Soho", 430, 258, SC_D, 0, True),
    ("Covent Garden", 452, 288, SC_D, 0, True),
    ("The City", 792, 186, SC_D, 0, True),
    ("South Bank", 592, 356, SC_D, 0, True),
    ("Marylebone Road", 163, 141, IT, -4, True),
    ("Oxford Street", 345, 225, IT, -10, True),
    ("Fleet Street", 572, 234, IT, -11, True),
]
CHAR_W = {SC_D: 10.4, IT: 5.5}
LINE_H = {SC_D: 15, IT: 13}

clearings = []  # (cx, cy_mid, w, h, rot)
def clearing(cx, y_baseline, text, kind, rot=0, pad_w=10, pad_h=5):
    w = len(text) * CHAR_W[kind] + pad_w
    h = LINE_H[kind] + pad_h
    clearings.append((cx, y_baseline - LINE_H[kind] * 0.36, w, h, rot))

for text, x, y, kind, rot, clear in LABELS:
    if clear:
        clearing(x, y, text, kind, rot)
# venue labels and notes
clearing(216, 122, "Old Marylebone Town Hall", SC_D, pad_w=14, pad_h=9)
clearing(216, 176, "the ceremony", IT, pad_w=12, pad_h=8)
clearing(714, 221, "The Ned", SC_D, pad_w=16, pad_h=10)
clearing(714, 275, "the reception", IT, pad_w=12, pad_h=8)
clearing(cab_x + 5, cab_y - 27, "black cabs, provided", IT, pad_w=14, pad_h=8)
clearing(654, 262, "St Paul's", IT, pad_w=10, pad_h=6)
# the venue name clearings above use SC_D char width but venue SC is 21px:
clearings[-6] = (216, 122 - 8, 24 * 14.2 + 16, 26, 0)
clearings[-4] = (714, 221 - 8, 7 * 14.2 + 18, 26, 0)

mask_rects = "".join(
    f'<rect x="{cx - w/2:.0f}" y="{cy - h/2:.0f}" width="{w:.0f}" height="{h:.0f}"'
    + (f' transform="rotate({rot} {cx:.0f} {cy:.0f})"' if rot else "") + "></rect>"
    for cx, cy, w, h, rot in clearings)

# collision audit: road points inside clearings, before masking
def in_clearing(p):
    for cx, cy, w, h, rot in clearings:
        a = math.radians(-rot)
        dx, dy = p[0] - cx, p[1] - cy
        rx = dx * math.cos(a) - dy * math.sin(a)
        ry = dx * math.sin(a) + dy * math.cos(a)
        if abs(rx) < w / 2 and abs(ry) < h / 2:
            return True
    return False
n_hits = sum(1 for cls in buckets.values() for ch in cls for p in ch if in_clearing(p))
print(f"label clearings: {len(clearings)}, road points masked out beneath them: {n_hits}")

# ── assemble ───────────────────────────────────────────────────────
parts = []
A = parts.append
A('<defs><clipPath id="mapclip"><rect x="8" y="8" width="884" height="441"></rect></clipPath>'
  f'<mask id="labelmask"><rect x="0" y="0" width="900" height="457" fill="#fff"></rect>'
  f'<g fill="#000">{mask_rects}</g></mask></defs>')
A('<rect x="8" y="8" width="884" height="441" fill="none" stroke="#1d1a16" stroke-opacity="0.3" stroke-width="1"></rect>')
A('<g clip-path="url(#mapclip)">')
A('<g fill="#1d1a16" fill-opacity="0.055" stroke="#1d1a16" stroke-opacity="0.13" stroke-width="0.7">')
for p in parks:
    A(f'<path d="{path_d(p, True)}"></path>')
A('</g>')
A(f'<path d="{path_d(thames)}" fill="none" stroke="#1d1a16" stroke-opacity="0.05" stroke-width="30" stroke-linecap="round" stroke-linejoin="round"></path>')
A(f'<path id="thamespath" d="{path_d(thames)}" fill="none" stroke="#1d1a16" stroke-opacity="0.10" stroke-width="19" stroke-linecap="round" stroke-linejoin="round"></path>')
A('<g fill="#1d1a16" fill-opacity="0.11" stroke="#1d1a16" stroke-opacity="0.2" stroke-width="0.6">')
for p in lakes:
    A(f'<path d="{path_d(p, True)}"></path>')
A('</g>')
A('<g mask="url(#labelmask)">')
for cls, (op, wdt) in {"secondary": (0.08, 0.75), "primary": (0.14, 1.1),
                       "trunk": (0.20, 1.5)}.items():
    A(f'<g fill="none" stroke="#1d1a16" stroke-opacity="{op}" stroke-width="{wdt}" stroke-linecap="round" stroke-linejoin="round">')
    for p in buckets[cls]:
        A(f'<path d="{path_d(p)}"></path>')
    A('</g>')
A(f'<path d="{path_d(route)}" fill="none" stroke="#1d1a16" stroke-opacity="0.55" stroke-width="1.6" stroke-dasharray="2 6" stroke-linecap="round" stroke-linejoin="round"></path>')
A('</g>')
A('</g>')

def sc_label(text, x, y):
    return (f'<text x="{x}" y="{y}">{text}</text>')

esc = lambda s: s.replace("'", "&rsquo;")
district_texts = "".join(
    f'<text x="{x}" y="{y}">{esc(t)}</text>'
    for t, x, y, kind, rot, _ in LABELS if kind == SC_D)
street_texts = "".join(
    f'<text x="{x}" y="{y}" transform="rotate({rot} {x} {y})">{t}</text>'
    for t, x, y, kind, rot, _ in LABELS if kind == IT)

overlay = f'''
          <text font-family="'Cormorant Garamond', serif" font-style="italic" font-size="15.5" letter-spacing="1.5" fill="#1d1a16" opacity="0.55">
            <textPath href="#thamespath" startOffset="42%">The Thames</textPath>
          </text>
          <g font-family="'Cormorant SC', serif" font-size="13" letter-spacing="3" fill="#1d1a16" opacity="0.42" text-anchor="middle">{district_texts}</g>
          <g font-family="'Cormorant Garamond', serif" font-style="italic" font-size="12" fill="#1d1a16" opacity="0.55" text-anchor="middle">{street_texts}</g>
          <g fill="#1d1a16" opacity="0.6">
            <rect x="473" y="352" width="5" height="21"></rect>
            <path d="M471.5,352 L480,352 L475.5,343 Z"></path>
            <rect x="471.5" y="356" width="8" height="5" fill="#ece7d8" stroke="#1d1a16" stroke-width="0.8"></rect>
          </g>
          <g stroke="#1d1a16" stroke-opacity="0.5" fill="none">
            <circle cx="516" cy="362" r="9" stroke-width="1.2"></circle>
            <path d="M516,353 L516,371 M507,362 L525,362 M509.6,355.6 L522.4,368.4 M522.4,355.6 L509.6,368.4" stroke-width="0.7"></path>
            <path d="M511,374 L516,367 L521,374" stroke-width="1.1"></path>
          </g>
          <g stroke="#1d1a16" stroke-opacity="0.5" stroke-width="1.1" fill="none">
            <path d="M239,255 L239,246 A 5 5 0 0 1 249,246 L249,255"></path>
            <path d="M236,255 L252,255"></path>
          </g>
          <rect x="805" y="324" width="4.5" height="6" fill="#1d1a16" opacity="0.6"></rect>
          <rect x="809" y="335" width="4.5" height="6" fill="#1d1a16" opacity="0.6"></rect>
          <g stroke="#1d1a16" stroke-opacity="0.55" stroke-width="0.9" fill="none">
            <path d="M645,241 L663,241"></path>
            <path d="M647,241 A 7 7 0 0 1 661,241"></path>
            <path d="M654,234 L654,229 M652,231 L656,231"></path>
          </g>
          <text x="654" y="262" text-anchor="middle" font-family="'Cormorant Garamond', serif" font-style="italic" font-size="13.5" fill="#1d1a16" opacity="0.55">St Paul&rsquo;s</text>
          <g transform="translate({cab_x - 17},{cab_y - 17})">
            <path d="M2,14 Q0,14 0,11 L0,8 Q0,5 4,5 L9,5 L12,1.5 Q12.5,0.5 14,0.5 L25,0.5 Q29,0.5 30.5,3.5 L31.5,5 Q34,5.5 34,8 L34,11 Q34,14 32,14 Z" fill="#1d1a16"></path>
            <path d="M14.5,2 L24,2 L24,5 L13,5 Z M25.5,2.4 L28.5,4.6 L25.5,4.6 Z" fill="#ece7d8"></path>
            <circle cx="8.5" cy="14" r="3.2" fill="#1d1a16"></circle>
            <circle cx="8.5" cy="14" r="1.2" fill="#ece7d8"></circle>
            <circle cx="26.5" cy="14" r="3.2" fill="#1d1a16"></circle>
            <circle cx="26.5" cy="14" r="1.2" fill="#ece7d8"></circle>
          </g>
          <text x="{cab_x + 5}" y="{cab_y - 22}" text-anchor="middle" font-family="'Cormorant Garamond', serif" font-style="italic" font-size="14.5" fill="#1d1a16" opacity="0.7">black cabs, provided</text>
          <g>
            <ellipse cx="216" cy="147" rx="8.5" ry="9.5" fill="#ece7d8" stroke="#1d1a16" stroke-width="0.9" stroke-opacity="0.65"></ellipse>
            <rect x="212.5" y="143.5" width="7" height="7" fill="#1d1a16" transform="rotate(45 216 147)"></rect>
            <text x="216" y="122" text-anchor="middle" font-family="'Cormorant SC', serif" font-size="21" letter-spacing="1.8" fill="#1d1a16">Old Marylebone Town Hall</text>
            <text x="216" y="176" text-anchor="middle" font-family="'Cormorant Garamond', serif" font-style="italic" font-size="15" fill="#1d1a16" opacity="0.6">the ceremony</text>
          </g>
          <g>
            <ellipse cx="714" cy="246" rx="8.5" ry="9.5" fill="#ece7d8" stroke="#1d1a16" stroke-width="0.9" stroke-opacity="0.65"></ellipse>
            <rect x="710.5" y="242.5" width="7" height="7" fill="#1d1a16" transform="rotate(45 714 246)"></rect>
            <text x="714" y="221" text-anchor="middle" font-family="'Cormorant SC', serif" font-size="21" letter-spacing="1.8" fill="#1d1a16">The Ned</text>
            <text x="714" y="275" text-anchor="middle" font-family="'Cormorant Garamond', serif" font-style="italic" font-size="15" fill="#1d1a16" opacity="0.6">the reception</text>
          </g>
          <g transform="translate(858,52)">
            <path d="M0,-14 L4,0 L0,14 L-4,0 Z" fill="#1d1a16" opacity="0.55"></path>
            <path d="M0,-18 L0,18 M-11,0 L11,0" stroke="#1d1a16" stroke-opacity="0.3" stroke-width="0.8"></path>
            <text x="0" y="-24" text-anchor="middle" font-family="'Cormorant SC', serif" font-size="13" fill="#1d1a16" opacity="0.6">N</text>
          </g>
          <g stroke="#1d1a16" stroke-opacity="0.45" stroke-width="1">
            <path d="M32,420 L190,420 M32,415 L32,425 M190,415 L190,425 M111,417 L111,423"></path>
          </g>
          <text x="111" y="440" text-anchor="middle" font-family="'Cormorant Garamond', serif" font-style="italic" font-size="13.5" fill="#1d1a16" opacity="0.55">one mile</text>'''

frag = "\n          ".join(parts)
figure = ('      <figure class="map-fig" role="img" aria-label="Street map of central London in the wedding\'s ink-on-paper style: the real road network, the Thames, and the black-cab route east from Old Marylebone Town Hall past Soho and St Paul\'s to The Ned">\n'
          '        <svg viewBox="0 0 900 457" aria-hidden="true" focusable="false">\n'
          '          ' + frag + overlay + '\n        </svg>\n'
          '        <figcaption>Marylebone to the City &mdash; four miles east by black cab, on us</figcaption>\n'
          '      </figure>')

idx = ROOT / "index.html"
t = idx.read_text()
start = t.index('      <figure class="map-fig"')
end = t.index('</figure>', start) + len('</figure>')
idx.write_text(t[:start] + figure + t[end:])
print(f"map rebuilt into index.html ({len(figure)//1024} KB figure)")
