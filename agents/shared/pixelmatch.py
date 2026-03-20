#!/usr/bin/env python3
"""
Pixel-level diff between a Figma design PNG and a rendered screenshot.

Handles the 2x scale difference: Figma exports at @2x, rendered screenshots are @1x.
Scales Figma down to match rendered dimensions before comparing.

Usage:
    # Full-page diff
    python3 agents/shared/pixelmatch.py <figma_png> <rendered_png> <diff_output>

    # Per-component diff using a regions JSON file
    python3 agents/shared/pixelmatch.py <figma_png> <rendered_png> <diff_output> --regions <regions.json>

Output (stdout, JSON):
    {
      "score": 97,              # 0-100, higher = more similar
      "diff_pixels": 1240,      # number of pixels that differ
      "total_pixels": 518400,
      "diff_pct": 0.24,
      "diff_image": "/tmp/diff-output.png",
      "regions": {              # only if --regions provided
        "navbar": { "score": 99, "diff_pixels": 45 },
        "school_health": { "score": 85, "diff_pixels": 890 }
      }
    }
"""

import sys
import json
import math
import argparse
import os
from PIL import Image, ImageDraw


PIXEL_THRESHOLD = 0.10   # colour distance 0-1; below this = same pixel
ANTIALIAS_RADIUS = 1     # ignore 1-pixel antialiasing halos


def colour_distance(p1: tuple, p2: tuple) -> float:
    """Normalised Euclidean distance between two RGB(A) pixels (0-1)."""
    r = (p1[0] - p2[0]) ** 2
    g = (p1[1] - p2[1]) ** 2
    b = (p1[2] - p2[2]) ** 2
    return math.sqrt(r + g + b) / math.sqrt(3 * 255 ** 2)


def is_antialiased(img, x: int, y: int, width: int, height: int) -> bool:
    """Return True if the pixel looks like part of an antialiased edge."""
    min_x = max(0, x - ANTIALIAS_RADIUS)
    max_x = min(width - 1, x + ANTIALIAS_RADIUS)
    min_y = max(0, y - ANTIALIAS_RADIUS)
    max_y = min(height - 1, y + ANTIALIAS_RADIUS)
    px = img.getpixel((x, y))
    for ny in range(min_y, max_y + 1):
        for nx in range(min_x, max_x + 1):
            if nx == x and ny == y:
                continue
            npx = img.getpixel((nx, ny))
            if colour_distance(px, npx) > 0.1:
                return True
    return False


def diff_images(img1: Image.Image, img2: Image.Image) -> tuple[Image.Image, int]:
    """
    Compare two same-sized images.
    Returns (diff_image, diff_pixel_count).
    diff_image: grey base + red overlay where pixels differ.
    """
    w, h = img1.size
    diff = Image.new("RGB", (w, h))
    diff_pixels = 0

    pixels1 = img1.load()
    pixels2 = img2.load()
    diff_p = diff.load()

    for y in range(h):
        for x in range(w):
            p1 = pixels1[x, y][:3]
            p2 = pixels2[x, y][:3]
            dist = colour_distance(p1, p2)

            if dist < PIXEL_THRESHOLD:
                # Same — render grey-dimmed version of original
                grey = int(0.1 * p1[0] + 0.1 * p1[1] + 0.1 * p1[2])
                diff_p[x, y] = (grey + 180, grey + 180, grey + 180)
            else:
                aa1 = is_antialiased(img1, x, y, w, h)
                aa2 = is_antialiased(img2, x, y, w, h)
                if aa1 or aa2:
                    # Antialiasing — render yellow (warning, not error)
                    diff_p[x, y] = (255, 215, 0)
                else:
                    # Real difference — red
                    diff_p[x, y] = (255, 0, 0)
                    diff_pixels += 1

    return diff, diff_pixels


def load_and_align(figma_path: str, rendered_path: str) -> tuple[Image.Image, Image.Image]:
    """
    Load both images and align them:
    - Figma is @2x so scale it down by 0.5
    - Crop both to the same (min) dimensions
    """
    figma = Image.open(figma_path).convert("RGBA")
    rendered = Image.open(rendered_path).convert("RGBA")

    # Scale figma down by 2x
    fw, fh = figma.size
    figma = figma.resize((fw // 2, fh // 2), Image.LANCZOS)

    # Crop to minimum shared dimensions
    w = min(figma.width, rendered.width)
    h = min(figma.height, rendered.height)
    figma = figma.crop((0, 0, w, h))
    rendered = rendered.crop((0, 0, w, h))

    return figma, rendered


def diff_region(figma: Image.Image, rendered: Image.Image,
                x: int, y: int, x2: int, y2: int) -> dict:
    """Diff a specific crop region. Coordinates in @1x rendered pixels."""
    w, h = figma.size
    cx1, cy1 = max(0, x), max(0, y)
    cx2, cy2 = min(w, x2), min(h, y2)

    f_crop = figma.crop((cx1, cy1, cx2, cy2))
    r_crop = rendered.crop((cx1, cy1, cx2, cy2))

    _, diff_px = diff_images(f_crop, r_crop)
    total = (cx2 - cx1) * (cy2 - cy1)
    score = round(100 - (diff_px / total * 100), 1) if total > 0 else 100

    return {"score": score, "diff_pixels": diff_px, "total_pixels": total}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("figma_png")
    parser.add_argument("rendered_png")
    parser.add_argument("diff_output")
    parser.add_argument("--regions", help="Path to JSON file defining crop regions")
    args = parser.parse_args()

    figma, rendered = load_and_align(args.figma_png, args.rendered_png)

    # Full-page diff
    diff_img, diff_px = diff_images(figma, rendered)
    total_px = figma.width * figma.height
    diff_pct = round(diff_px / total_px * 100, 2)
    score = round(100 - diff_pct, 1)

    os.makedirs(os.path.dirname(os.path.abspath(args.diff_output)), exist_ok=True)
    diff_img.save(args.diff_output)

    result = {
        "score": score,
        "diff_pixels": diff_px,
        "total_pixels": total_px,
        "diff_pct": diff_pct,
        "diff_image": args.diff_output,
        "figma_scaled_size": list(figma.size),
        "rendered_size": list(rendered.size),
    }

    # Per-region breakdown
    if args.regions:
        with open(args.regions) as f:
            regions = json.load(f)
        result["regions"] = {}
        for name, coords in regions.items():
            if name.startswith("_"):
                continue
            x, y, x2, y2 = coords
            result["regions"][name] = diff_region(figma, rendered, x, y, x2, y2)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
