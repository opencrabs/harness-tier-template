#!/usr/bin/env python3
"""Compose the coding-harness tier list.

Reads config.json + assets/, writes output/board.png.
All geometry constants below were measured pixel-exact from the approved
2026-10-05 board (1120x1048). Do not eyeball-edit them; re-measure instead.

Requires: python3 -m pip install pillow
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(ROOT, "config.json")
ASSETS = os.path.join(ROOT, "assets")
OUT_PATH = os.path.join(ROOT, "output", "board.png")

# ---- geometry (measured, not guessed) ----
W = 1120
FRAME_INSET, FRAME_T = 8, 3
GOLD = (201, 169, 97)
BG = (13, 13, 16)
CARD_BG = (32, 32, 38)
LABEL_COLOR = (235, 235, 240)
TAG_TEXT = (0, 0, 0)
TAG_X, TAG_W, TAG_H = 26, 150, 112
TAG_TEXT_CY = 52
ROW_Y0, ROW_PITCH = 158, 122
CARD_W, CARD_H, CARD_R = 160, 96, 10
COL_X = [186, 356]
ICON_DX, ICON_DY, ICON_S = 10, 15, 66
LABEL_DX, LABEL_PAD_R = 85, 10
TITLE_SIZE, TITLE_Y = 52, 45
SUB_SIZE, SUB_Y = 20, 112
GOLD_BAR_Y0, GOLD_BAR_Y1 = 144, 148
BOTTOM_MARGIN = 36


def load_font(size, bold=True):
    if bold:
        cands = [
            ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", None),
            ("/Library/Fonts/Arial Bold.ttf", None),
            ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", None),
        ]
    else:
        cands = [
            ("/System/Library/Fonts/Supplemental/Arial.ttf", None),
            ("/Library/Fonts/Arial.ttf", None),
            ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", None),
        ]
    for path, idx in cands:
        if os.path.exists(path):
            try:
                if idx is not None:
                    return ImageFont.truetype(path, size, index=idx)
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def card_rects(cfg):
    """Card rectangles in config order: [(x0, y0, x1, y1, entry), ...]"""
    rects = []
    for i, tier in enumerate(cfg["tiers"]):
        y0 = ROW_Y0 + i * ROW_PITCH
        for j, e in enumerate(tier["entries"]):
            x0 = COL_X[j]
            rects.append((x0, y0, x0 + CARD_W - 1, y0 + CARD_H - 1, e))
    return rects


def normalize_logo(name):
    """Any image in -> exact 66x66 slot (contain-fit, centered)."""
    path = os.path.join(ASSETS, name)
    if not os.path.exists(path):
        sys.exit(f"missing asset: assets/{name}")
    im = Image.open(path).convert("RGBA")
    if im.size != (ICON_S, ICON_S):
        im.thumbnail((ICON_S, ICON_S), Image.LANCZOS)
        slot = Image.new("RGBA", (ICON_S, ICON_S), (0, 0, 0, 0))
        off = ((ICON_S - im.width) // 2, (ICON_S - im.height) // 2)
        slot.paste(im, off, im)
        im = slot
    return im


def fit_label(draw, text, max_w):
    """12px standard, shrinking only until the text fits max_w (v6 rule)."""
    for size in (12, 11, 10, 9, 8, 7, 6):
        font = load_font(size, bold=True)
        x0, _, x1, _ = draw.textbbox((0, 0), text, font=font)
        if x1 - x0 <= max_w:
            return font
    return load_font(6, bold=True)


def compose():
    cfg = json.load(open(CFG_PATH))
    for t in cfg["tiers"]:
        if len(t["entries"]) > len(COL_X):
            sys.exit(f"tier {t['name']}: max {len(COL_X)} entries per row")

    H = ROW_Y0 + len(cfg["tiers"]) * ROW_PITCH + BOTTOM_MARGIN
    board = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(board)

    # header + frame
    d.rectangle([FRAME_INSET, FRAME_INSET, W - 1 - FRAME_INSET, H - 1 - FRAME_INSET],
                outline=GOLD, width=FRAME_T)
    d.text((W / 2, TITLE_Y), cfg["title"], font=load_font(TITLE_SIZE),
           fill=(240, 240, 245), anchor="ma")
    d.text((W / 2, SUB_Y), cfg["subtitle"], font=load_font(SUB_SIZE),
           fill=(160, 160, 170), anchor="ma")
    d.rectangle([FRAME_INSET + FRAME_T, GOLD_BAR_Y0, W - 1 - FRAME_INSET - FRAME_T,
                 GOLD_BAR_Y1], fill=GOLD)

    for i, tier in enumerate(cfg["tiers"]):
        y0 = ROW_Y0 + i * ROW_PITCH
        # tier tag: full-height color band; text color follows bg luminance
        c = tuple(tier["color"])
        lum = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
        d.rounded_rectangle([TAG_X, y0, TAG_X + TAG_W, y0 + TAG_H],
                            radius=CARD_R, fill=c)
        d.text((TAG_X + TAG_W / 2, y0 + TAG_TEXT_CY), tier["name"],
               font=load_font(45, bold=True),
               fill=TAG_TEXT if lum >= 150 else (255, 255, 255), anchor="mm")
        # cards
        for j, e in enumerate(tier["entries"]):
            x0 = COL_X[j]
            d.rounded_rectangle([x0, y0, x0 + CARD_W - 1, y0 + CARD_H - 1],
                                radius=CARD_R, fill=CARD_BG)
            board.paste(normalize_logo(e["logo"]), (x0 + ICON_DX, y0 + ICON_DY),
                        normalize_logo(e["logo"]))
            font = fit_label(d, e["name"], CARD_W - LABEL_DX - LABEL_PAD_R)
            d.text((x0 + LABEL_DX, y0 + CARD_H / 2), e["name"], font=font,
                   fill=LABEL_COLOR, anchor="lm")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    board.save(OUT_PATH)
    print(f"wrote {OUT_PATH} ({W}x{H}, {len(card_rects(cfg))} cards)")


if __name__ == "__main__":
    compose()
