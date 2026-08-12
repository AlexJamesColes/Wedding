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


def build():
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
    width: 29.7cm; height: 21cm; margin: 0 auto; padding: 2cm 2.4cm 1.8cm;
    background: #f7f4ec; position: relative; text-align: center;
    display: flex; flex-direction: column; justify-content: center;
    box-shadow: 0 16px 44px rgba(0,0,0,.22);
  }
  .sheet::before {
    content: ""; position: absolute; inset: 1.1cm;
    border: 0.6pt solid rgba(29,26,22,.4); pointer-events: none;
  }
  .title {
    font-family: "Snell Roundhand", "Edwardian Script ITC", "Apple Chancery", cursive;
    font-size: 42pt; line-height: 1.05;
  }
  .orn { margin: 16pt auto 0; width: 96pt; display: flex; align-items: center; gap: 8pt; }
  .orn::before, .orn::after { content: ""; flex: 1; height: 0.6pt; background: var(--ink); opacity: .3; }
  .orn span { width: 4pt; height: 4pt; background: var(--ink); opacity: .65; transform: rotate(45deg); }
  .tables { display: flex; justify-content: center; gap: 2.4cm; margin-top: 24pt; }
  h2 {
    font-family: "Cormorant SC", serif; font-weight: 400; font-size: 13.5pt;
    letter-spacing: .12em; text-indent: .12em; margin: 0 0 12pt;
  }
  .sides { display: flex; align-items: stretch; }
  .side { width: 5cm; padding: 0 0.35cm; }
  .side p { margin: 0; font-style: italic; font-size: 12.5pt; line-height: 1.7; white-space: nowrap; }
  .rule {                                  /* the table itself, seen from above */
    width: 0.34cm; align-self: stretch; margin: 2pt 0;
    border-left: 0.6pt solid rgba(29,26,22,.5);
    border-right: 0.6pt solid rgba(29,26,22,.5);
  }
  .mark {
    font-family: "Cormorant SC", serif; font-size: 9.5pt;
    letter-spacing: .3em; text-indent: .3em; color: #6e665a; margin: 26pt 0 0;
  }
  @media print {
    @page { size: A4 landscape; margin: 0; }
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
       "blocks": "".join(blocks)}

    (HERE / "table-plan.html").write_text(html)
    pdf = HERE / "The Tables, A4 landscape.pdf"
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", f"file://{HERE / 'table-plan.html'}"],
                   capture_output=True, check=True)
    seated = sum(len(s) for _, sides in TABLES for s in sides)
    print("wrote table-plan.html and the PDF |", seated, "guests seated")


if __name__ == "__main__":
    build()
