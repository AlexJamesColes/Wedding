#!/usr/bin/env python3
"""Render the C & A seal artwork (approved design G2·4) from macOS Didot.

Outputs:
  assets/img/seal.png      hero/404 seal — double ring, apex diamond, date band
  assets/img/amp.png       the seal's italic ampersand alone (nav wordmark)
  favicon.ico              16/32/48 — circular paper disc, transparent corners
  apple-touch-icon.png     180 — opaque paper square (iOS masks its own corners)

Optical correction: the italic ampersand leans right, so the A is nudged
inward (cx 0.762, not the geometric 0.785) and the C out a hair (0.218)
to make the two gaps read equal.
"""
from PIL import Image, ImageDraw, ImageFont
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAPER = (236, 231, 216, 255)
INK = (29, 26, 22, 255)
CLEAR = (0, 0, 0, 0)
DID = "/System/Library/Fonts/Didot.ttc"

C_X, A_X = 0.209, 0.753  # optically corrected: measured ink gaps, blend of min/mean equalisation


def bl(d, baseline, text, font, fill, cx):
    b = d.textbbox((0, 0), text, font=font)
    asc = font.getmetrics()[0]
    d.text((cx - (b[2] - b[0]) / 2 - b[0], baseline - asc), text, font=font, fill=fill)


def tracked(d, cx, y, text, font, fill, tracking):
    widths = [d.textlength(c, font=font) for c in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for c, w in zip(text, widths):
        d.text((x, y), c, font=font, fill=fill)
        x += w + tracking


def letters(d, S, baseline, lf_frac, af_frac, fill, li=0, ai=1):
    lf = ImageFont.truetype(DID, int(S * lf_frac), li)
    af = ImageFont.truetype(DID, int(S * af_frac), ai)
    bl(d, baseline, "&", af, fill, S / 2)
    bl(d, baseline, "C", lf, fill, S * C_X)
    bl(d, baseline, "A", lf, fill, S * A_X)


def hero_seal(S=800):
    H = int(S * 1.14)
    im = Image.new("RGBA", (S, H), CLEAR)
    d = ImageDraw.Draw(im)
    m = S * 0.045
    d.ellipse([m, m * 0.75, S - m, S - m * 0.75], outline=INK, width=max(1, S // 60))
    m2 = S * 0.085
    d.ellipse([m2, m2 * 0.78, S - m2, S - m2 * 0.78], outline=INK, width=max(1, S // 110))
    r = S * 0.045; cy = m * 0.75
    im.paste(CLEAR, (int(S / 2 - r * 1.6), int(cy - r * 1.4), int(S / 2 + r * 1.6), int(cy + r * 1.4)))
    d.polygon([(S / 2, cy - r), (S / 2 + r, cy), (S / 2, cy + r), (S / 2 - r, cy)], fill=INK)
    letters(d, S, S * 0.645, 0.24, 0.42, INK)
    df = ImageFont.truetype(DID, int(S * 0.052), 0)
    tracked(d, S / 2, S * 1.035, "XIV · AUG · MMXXVI", df, (29, 26, 22, 200), S * 0.018)
    return im


def round_favicon(S, tiny=False):
    """Paper disc with circular ring; transparent outside the disc."""
    im = Image.new("RGBA", (S, S), CLEAR)
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, S - 1, S - 1], fill=PAPER)
    ring_w = S // 22 if tiny else max(1, S // 48)
    m = S * 0.045
    d.ellipse([m, m, S - m, S - m], outline=INK, width=ring_w)
    if not tiny:
        m2 = S * 0.10
        d.ellipse([m2, m2, S - m2, S - m2], outline=INK, width=max(1, S // 110))
    if tiny:
        letters(d, S, S * 0.66, 0.38, 0.60, INK, li=2, ai=2)
    else:
        letters(d, S, S * 0.655, 0.26, 0.44, INK)
    return im


def touch_icon(S=720):
    im = Image.new("RGBA", (S, S), PAPER)
    d = ImageDraw.Draw(im)
    m = S * 0.045
    d.ellipse([m, m * 0.75, S - m, S - m * 0.75], outline=INK, width=max(1, S // 60))
    m2 = S * 0.085
    d.ellipse([m2, m2 * 0.78, S - m2, S - m2 * 0.78], outline=INK, width=max(1, S // 110))
    r = S * 0.045; cy = m * 0.75
    im.paste(PAPER, (int(S / 2 - r * 1.6), int(cy - r * 1.4), int(S / 2 + r * 1.6), int(cy + r * 1.4)))
    d.polygon([(S / 2, cy - r), (S / 2 + r, cy), (S / 2, cy + r), (S / 2 - r, cy)], fill=INK)
    letters(d, S, S * 0.645, 0.24, 0.42, INK)
    return im.convert("RGB")


def ampersand(S=320):
    im = Image.new("RGBA", (S, S), CLEAR)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(DID, int(S * 0.8), 1)
    b = d.textbbox((0, 0), "&", font=f)
    d.text((-b[0] + 2, -b[1] + 2), "&", font=f, fill=INK)
    return im.crop(im.getbbox())


def emboss_seal(S=480, date_band=False):
    """Blind-emboss variant: paper-coloured seal with baked light/shadow."""
    H = int(S * 1.14) if date_band else S
    mask = Image.new("L", (S, H), 0)
    d = ImageDraw.Draw(mask)
    m = S * 0.045
    d.ellipse([m, m * 0.75, S - m, S - m * 0.75], outline=255, width=max(1, S // 60))
    m2 = S * 0.085
    d.ellipse([m2, m2 * 0.78, S - m2, S - m2 * 0.78], outline=255, width=max(1, S // 110))
    r = S * 0.045; cy = m * 0.75
    mask.paste(0, (int(S / 2 - r * 1.6), int(cy - r * 1.4), int(S / 2 + r * 1.6), int(cy + r * 1.4)))
    d.polygon([(S / 2, cy - r), (S / 2 + r, cy), (S / 2, cy + r), (S / 2 - r, cy)], fill=255)
    lf = ImageFont.truetype(DID, int(S * 0.24), 0)
    af = ImageFont.truetype(DID, int(S * 0.42), 1)
    y = S * 0.645
    for text, font, cx in [("&", af, S / 2), ("C", lf, S * C_X), ("A", lf, S * A_X)]:
        b = d.textbbox((0, 0), text, font=font)
        asc = font.getmetrics()[0]
        d.text((cx - (b[2] - b[0]) / 2 - b[0], y - asc), text, font=font, fill=255)
    if date_band:
        df = ImageFont.truetype(DID, int(S * 0.052), 0)
        text = "XIV · AUG · MMXXVI"
        widths = [d.textlength(c, font=df) for c in text]
        total = sum(widths) + S * 0.018 * (len(text) - 1)
        x = S / 2 - total / 2
        for c, w in zip(text, widths):
            d.text((x, S * 1.035), c, font=df, fill=230)
            x += w + S * 0.018
    out = Image.new("RGBA", (S, H), CLEAR)
    sh = max(2, S // 110)
    dark = Image.new("RGBA", (S, H), (29, 26, 22, 70))
    light = Image.new("RGBA", (S, H), (255, 253, 246, 190))
    body = Image.new("RGBA", (S, H), (233, 228, 213, 255))
    shifted = Image.new("L", (S, H), 0); shifted.paste(mask, (sh, sh))
    out.paste(dark, (0, 0), shifted)
    shifted = Image.new("L", (S, H), 0); shifted.paste(mask, (-sh, -sh))
    out.paste(light, (0, 0), shifted)
    out.paste(body, (0, 0), mask)
    return out


hero_seal(800).resize((208, 237), Image.LANCZOS).save(ROOT / "assets/img/seal.png", optimize=True)
emboss_seal(480).resize((120, 120), Image.LANCZOS).save(ROOT / "assets/img/seal-emboss.png", optimize=True)
emboss_seal(880).resize((220, 220), Image.LANCZOS).save(ROOT / "assets/img/seal-emboss-lg.png", optimize=True)
amp = ampersand()
amp.resize((round(amp.width * 76 / amp.height), 76), Image.LANCZOS).save(
    ROOT / "assets/img/amp.png", optimize=True)
f48 = round_favicon(480).resize((48, 48), Image.LANCZOS)
f32 = round_favicon(320).resize((32, 32), Image.LANCZOS)
f16 = round_favicon(64, tiny=True).resize((16, 16), Image.LANCZOS)
f48.save(ROOT / "favicon.ico", sizes=[(48, 48), (32, 32), (16, 16)], append_images=[f32, f16])
touch_icon(720).resize((180, 180), Image.LANCZOS).save(ROOT / "apple-touch-icon.png", optimize=True)
print("seal.png, amp.png, favicon.ico (circular), apple-touch-icon.png written")
