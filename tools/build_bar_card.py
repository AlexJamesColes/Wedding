"""Builds the bar card in two forms from one source.

  bar-card.html          the card alone, page cut to 13 by 21cm
  bar-card-a4.html       the same card on A4 with a dashed line to cut along

Both print as ink only; the paper supplies the ground.
"""
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CUT_RULE = """  /* the trim line: the card's true 13 by 21 edge. Cut just inside it. */
  .card::after {
    content: ""; position: absolute; inset: 0;
    border: 0.4pt dashed rgba(29, 26, 22, .38); border-radius: 50%;
    pointer-events: none;
  }
"""

CAPTION_EXACT = ("Print at 100%, no scaling, on 13 by 21 centimetre stock. Leave background\n"
                 "  graphics switched off so the card prints as ink alone and your paper shows through.")
CAPTION_A4 = ("Print at 100%, no scaling, on A4 card, background graphics switched off. Cut along the dashed\n"
              "  oval, blade just inside it, and the card measures 13 by 21 centimetres. The fine solid line within is\n"
              "  engraving and stays on the card.")


def build():
    src = (HERE / "bar-card.html").read_text()

    # the exact-size card carries no cut line: the page edge is the cut
    exact = src
    exact = re.sub(r"\n  /\* the trim line.*?\n  \}\n", "\n", exact, flags=re.S)
    exact = re.sub(r"Print at 100%.*?(?=</p>)", CAPTION_EXACT, exact, flags=re.S)
    (HERE / "bar-card.html").write_text(exact)

    # the A4 sheet carries the card centred, with the cut line marked
    a4 = exact.replace("@page { size: 13cm 21cm; margin: 0; }", "@page { size: A4; margin: 0; }")
    a4 = a4.replace("  .mark {", CUT_RULE + "  .mark {")
    a4 = a4.replace(".card { background: none; box-shadow: none; }",
                    ".card { background: none; box-shadow: none; margin: 4.35cm auto 0; }")
    a4 = re.sub(r"Print at 100%.*?(?=</p>)", CAPTION_A4, a4, flags=re.S)
    (HERE / "bar-card-a4.html").write_text(a4)

    for html, pdf in [("bar-card.html", "The Bar, 13x21cm.pdf"),
                      ("bar-card-a4.html", "The Bar, A4 with cut guide.pdf")]:
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={HERE / pdf}", f"file://{HERE / html}"],
                       capture_output=True, check=True)
        print("wrote", pdf)


if __name__ == "__main__":
    build()
