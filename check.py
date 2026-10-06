#!/usr/bin/env python3
"""Verify output/board.png: no label overflows its card, uniform spacing.

The gate that caught the real bug (OpenCrabs label 18px past its card edge,
margins ranging 1..45px across cards). Run after every compose:

    python3 compose.py && python3 check.py

Exit 0 = clean, exit 1 = violation (prints the offenders).
"""
import json
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compose  # noqa: E402  (reuses geometry constants + card_rects)

ROOT = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(ROOT, "output", "board.png")
BRIGHT = 350  # label pixels: r+g+b > BRIGHT
SCAN_PAST = 12  # how many px past the card edge to scan for overflow


def main():
    cfg = json.load(open(os.path.join(ROOT, "config.json")))
    if not os.path.exists(BOARD):
        sys.exit("no output/board.png - run compose.py first")
    im = Image.open(BOARD).convert("RGB")
    px = im.load()

    print(f"{'entry':<20}{'right margin':>14}{'overflow px':>14}")
    bad = 0
    for x0, y0, x1, y1, e in compose.card_rects(cfg):
        cy0, cy1 = y0 + 20, y0 + compose.CARD_H - 20
        last_bright = None
        overflow = 0
        for xx in range(x0 + compose.LABEL_DX, min(x1 + SCAN_PAST, im.width)):
            for yy in range(cy0, cy1):
                if sum(px[xx, yy]) > BRIGHT:
                    if xx <= x1:
                        last_bright = max(last_bright or 0, xx)
                    else:
                        overflow += 1
        margin = (x1 - last_bright) if last_bright else -1
        ok = overflow == 0 and margin >= compose.LABEL_PAD_R - 1
        flag = "" if ok else "  <-- VIOLATION"
        if not ok:
            bad += 1
        print(f"{e['name']:<20}{margin:>12}px{overflow:>12}px{flag}")

    if bad:
        sys.exit(f"\nFAILED: {bad} label(s) violate card spacing")
    print("\nOK: all labels inside cards, min padding "
          f"{compose.LABEL_PAD_R - 1}px respected")


if __name__ == "__main__":
    main()
