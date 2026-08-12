"""The table plan as engraved stationery, A4 landscape, ink only.

The arrangement is held here so the plate can be rendered without the
planning tool. It matches the plan Chelsey and Alex settled on.
"""
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# each table, each side, in seat order from the fireplace end
TABLES = [
    ("Table One", [
        ["Pierre Albertyn", "Karen Coles", "Jake Virgo", "Alicia Connelly-Lopez",
         "Ross Albertyn", "Alara Guven", "Sam Houghton"],
        ["Jane Albertyn", "Jeremy Coles", "Emily Virgo", "Joel Connelly",
         "Georgie Albertyn", "Max Taylor", "Brittany Morel"],
    ]),
    ("Table Two", [
        ["Chiara Iorizzo", "James Steffens", "Ellie Dickens", "Thomas Bentley",
         "Monique Albertyn", "Scott Albertyn", "Sonam Mod", "Chris McPetrie"],
        ["Omkar Harmalkar", "Janine Weixler", "Ben Steffens", "Alex Coles",
         "Chelsey Coles", "Sarah Cawood", "James Hardesty", "Pascal McPetrie"],
    ]),
]


def faces():
    """Borrow the faces already embedded in the bar card."""
    src = (HERE / "bar-card.html").read_text()
    out = {}
    for fam, style in [("Cormorant Garamond", "normal"), ("Cormorant Garamond", "italic"),
                       ("Cormorant SC", "normal")]:
        m = re.search(r"font-family: '%s'; font-style: %s; font-weight: 400;\s*"
                      r"src: url\(\"(data:font/woff2;base64,[^\"]+)\"\)" % (re.escape(fam), style), src)
        out[(fam, style)] = m.group(1)
    return out


SHEETS = [                 # landscape, in centimetres
    ("A4", 29.7, 21.0),
    ("A3", 42.0, 29.7),
    ("A1", 84.1, 59.4),
    ("A0", 118.9, 84.1),
]


def build(label="A4", W=29.7, H=21.0):
    k = W / 29.7           # A4 landscape is the drawing; the rest is the same, larger
    f = faces()
    blocks = []
    for name, sides in TABLES:
        cols = "".join(
            '<div class="side">%s</div>' % "".join("<p>%s</p>" % n for n in side)
            for side in sides)
        blocks.append('<div class="table"><h2>%s</h2><div class="sides">%s'
                      '</div></div>' % (name, cols[:len(cols)//2] and
                                        cols.replace('</div><div class="side">',
                                                     '</div><div class="rule"></div><div class="side">')))
    def cm(v): return "%.3fcm" % (v * k)
    def pt(v): return "%.2fpt" % (v * k)
    html = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<title>Chelsey &amp; Alex &middot; The Tables</title>
<style>
  @font-face { font-family: 'Cormorant Garamond'; font-style: normal; font-weight: 400;
    src: url("%(cg)s") format('woff2'); }
  @font-face { font-family: 'Cormorant Garamond'; font-style: italic; font-weight: 400;
    src: url("%(cgi)s") format('woff2'); }
  @font-face { font-family: 'Cormorant SC'; font-style: normal; font-weight: 400;
    src: url("%(sc)s") format('woff2'); }
  :root { --ink: #1d1a16; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #ded7c9; padding: 30px 16px 50px;
    font-family: "Cormorant Garamond", Georgia, serif; color: var(--ink);
    font-feature-settings: "kern" 1, "liga" 1, "onum" 1;
  }
  .sheet {
    width: %(W)s; height: %(H)s; margin: 0 auto; padding: %(padT)s %(padX)s %(padB)s;
    background: #f7f4ec; position: relative; text-align: center;
    display: flex; flex-direction: column; justify-content: center;
    box-shadow: 0 16px 44px rgba(0,0,0,.22);
  }
  .sheet::before {
    content: ""; position: absolute; inset: %(inset)s;
    border: %(hair)s solid rgba(29,26,22,.4); pointer-events: none;
  }
  .title {
    font-family: "Snell Roundhand", "Edwardian Script ITC", "Apple Chancery", cursive;
    font-size: %(title)s; line-height: 1.05;
  }
  .orn { margin: %(ornTop)s auto 0; width: %(ornW)s; display: flex; align-items: center; gap: %(ornGap)s; }
  .orn::before, .orn::after { content: ""; flex: 1; height: %(hair)s; background: var(--ink); opacity: .3; }
  .orn span { width: %(diamond)s; height: %(diamond)s; background: var(--ink); opacity: .65; transform: rotate(45deg); }
  .tables { display: flex; justify-content: center; gap: %(tableGap)s; margin-top: %(tablesTop)s; }
  h2 {
    font-family: "Cormorant SC", serif; font-weight: 400; font-size: %(head)s;
    letter-spacing: .12em; text-indent: .12em; margin: 0 0 %(headGap)s;
  }
  .sides { display: flex; align-items: stretch; min-height: %(sidesH)s; }
  .side {
    width: %(colW)s; padding: 0 %(colPad)s; height: %(sidesH)s;
    display: flex; flex-direction: column; justify-content: space-between;
  }
  .side p { margin: 0; font-style: italic; font-size: %(name)s; line-height: 1.7; white-space: nowrap; }
  .rule {                                  /* the table itself, seen from above */
    width: %(ruleW)s; align-self: stretch; margin: %(ruleM)s 0;
    border-left: %(hair)s solid rgba(29,26,22,.5);
    border-right: %(hair)s solid rgba(29,26,22,.5);
  }
  .mark {
    font-family: "Cormorant SC", serif; font-size: %(mark)s;
    letter-spacing: .3em; text-indent: .3em; color: #6e665a; margin: %(markTop)s 0 0;
  }
  @media print {
    @page { size: %(W)s %(H)s; margin: 0; }
    body { background: none; padding: 0; }
    .sheet { margin: 0; box-shadow: none; background: none; }
  }
</style>
</head>
<body>
  <div class="sheet">
    <p class="title">The Tables</p>
    <div class="orn"><span></span></div>
    <div class="tables">%(blocks)s</div>
    <p class="mark">C &amp; A</p>
  </div>
</body>
</html>
""" % {"cg": f[("Cormorant Garamond", "normal")],
       "cgi": f[("Cormorant Garamond", "italic")],
       "sc": f[("Cormorant SC", "normal")],
       "blocks": "".join(blocks),
       "W": cm(29.7), "H": cm(21.0), "padT": cm(2), "padX": cm(2.4), "padB": cm(1.8),
       "inset": cm(1.1), "hair": pt(0.6), "title": pt(42), "ornTop": pt(16), "ornW": pt(96),
       "ornGap": pt(8), "diamond": pt(4), "tableGap": cm(2.4), "tablesTop": pt(24),
       "head": pt(13.5), "headGap": pt(12), "colW": cm(5), "colPad": cm(0.35),
       "name": pt(12.5), "ruleW": cm(0.34), "ruleM": pt(2), "sidesH": pt(8 * 12.5 * 1.7), "mark": pt(9.5), "markTop": pt(26)}

    (HERE / ("table-plan-%s.html" % label)).write_text(html)
    pdf = HERE / ("The Tables, %s landscape.pdf" % label)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", f"file://{HERE / ('table-plan-%s.html' % label)}"],
                   capture_output=True, check=True)
    print("wrote", pdf.name)


if __name__ == "__main__":
    for label, W, H in SHEETS:
        build(label, W, H)
    seated = sum(len(s) for _, sides in TABLES for s in sides)
    print(seated, "guests seated on every sheet")
