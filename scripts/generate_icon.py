"""One-off generator for snapflow/assets/icon.ico (run manually; not a runtime dependency)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "snapflow" / "assets" / "icon.ico"
SIZE = 256

BG_TOP = (28, 28, 32)
BG_BOTTOM = (13, 13, 13)
ACCENT = (10, 132, 255)
ACCENT_LIGHT = (90, 180, 255)


def build_base() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    grad = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
    for y in range(SIZE):
        t = y / (SIZE - 1)
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        ImageDraw.Draw(grad).line([(0, y), (SIZE, y)], fill=(r, g, b, 255))

    mask = Image.new("L", (SIZE, SIZE), 0)
    radius = int(SIZE * 0.22)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, SIZE - 1, SIZE - 1], radius=radius, fill=255
    )
    img.paste(grad, (0, 0), mask)

    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [1, 1, SIZE - 2, SIZE - 2], radius=radius, outline=(255, 255, 255, 28), width=2
    )

    bolt = [
        (0.58, 0.10), (0.30, 0.56), (0.46, 0.56),
        (0.40, 0.90), (0.74, 0.42), (0.56, 0.42),
    ]
    pts = [(x * SIZE, y * SIZE) for x, y in bolt]
    draw.polygon(pts, fill=ACCENT_LIGHT)

    return img


def main() -> None:
    base = build_base()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    base.save(OUT, format="ICO", sizes=[(s, s) for s in sizes])
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
