#!/usr/bin/env python3
"""Render the editable, high-resolution version of Unzipping Dawn.

Pillow is only needed while developing the artwork. The competition entry
itself is the committed PNG and main.py copies it using the standard library.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "entry.png"
SIZE = 1024
UPSCALE = 2
WORK_SIZE = SIZE * UPSCALE
SEED = 20261112
Point = tuple[float, float]
RGB = tuple[int, int, int]


def blend(start: RGB, end: RGB, amount: float) -> RGB:
    """Interpolate two colors with a clamped weight."""
    t = min(1.0, max(0.0, amount))
    return tuple(round(a + (b - a) * t) for a, b in zip(start, end))


def gradient(top: RGB, bottom: RGB) -> Image.Image:
    """Build a smooth vertical night-sky gradient."""
    strip = Image.new("RGB", (1, WORK_SIZE))
    pixels = strip.load()
    for y in range(WORK_SIZE):
        pixels[0, y] = blend(top, bottom, y / (WORK_SIZE - 1))
    return strip.resize((WORK_SIZE, WORK_SIZE))


def to_canvas(point: Point) -> tuple[int, int]:
    return round(point[0] * UPSCALE), round(point[1] * UPSCALE)


def zipper_point(u: float, v: float) -> Point:
    """Map zipper-local coordinates onto the image's rising diagonal."""
    diagonal = math.sqrt(0.5)
    return (132 + diagonal * (u + v), 875 + diagonal * (-u + v))


def mapped(points: Iterable[Point]) -> list[tuple[int, int]]:
    return [to_canvas(zipper_point(u, v)) for u, v in points]


def line_local(draw: ImageDraw.ImageDraw, points: Sequence[Point], color, width: float) -> None:
    draw.line(mapped(points), fill=color, width=max(1, round(width * UPSCALE)), joint="curve")


def polygon_local(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    color,
    outline=None,
    width: float = 1,
) -> None:
    vertices = mapped(points)
    draw.polygon(vertices, fill=color)
    if outline is not None:
        draw.line(vertices + [vertices[0]], fill=outline,
                  width=max(1, round(width * UPSCALE)), joint="curve")


def quadratic_curve(a: Point, control: Point, b: Point, steps: int = 32) -> list[Point]:
    curve = []
    for index in range(steps + 1):
        t = index / steps
        inverse = 1 - t
        curve.append((
            inverse * inverse * a[0] + 2 * inverse * t * control[0] + t * t * b[0],
            inverse * inverse * a[1] + 2 * inverse * t * control[1] + t * t * b[1],
        ))
    return curve


def soft_glow(
    image: Image.Image,
    center: Point,
    radius: float,
    color: RGB,
    opacity: int,
    blur: float,
) -> None:
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    x, y = to_canvas(center)
    r = round(radius * UPSCALE)
    draw.ellipse((x - r, y - r, x + r, y + r), fill=(*color, opacity))
    image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur * UPSCALE)))


def paint_sky() -> Image.Image:
    image = gradient((8, 13, 43), (7, 26, 47)).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    # Angular pools of blue give the dark fabric depth without competing
    # with the bright opening.
    draw.polygon([(0, 0), (WORK_SIZE, 0), (0, 340 * UPSCALE)], fill=(39, 53, 112, 42))
    draw.polygon([(0, 1430 * UPSCALE // 2), (390 * UPSCALE, WORK_SIZE),
                  (0, WORK_SIZE)], fill=(0, 144, 167, 38))
    draw.polygon([(1280 * UPSCALE // 2, WORK_SIZE), (WORK_SIZE, 750 * UPSCALE),
                  (WORK_SIZE, WORK_SIZE)], fill=(0, 133, 157, 40))
    soft_glow(image, (804, 837), 106, (27, 167, 190), 46, 24)

    stars = random.Random(SEED)
    for _ in range(120):
        x = stars.randrange(12, SIZE - 12)
        y = stars.randrange(12, SIZE - 12)
        along = (x + y - 1007) / math.sqrt(2)
        across = (x - y + 743) / math.sqrt(2)
        if 235 < along < 1150 and abs(across) < 142:
            continue
        radius = stars.choice((1, 1, 1, 2, 2, 3)) * UPSCALE // 2
        alpha = stars.choice((48, 65, 90, 125))
        draw.ellipse((x * UPSCALE - radius, y * UPSCALE - radius,
                      x * UPSCALE + radius, y * UPSCALE + radius),
                     fill=(211, 239, 255, alpha))
    return image


def opening_width(x: float) -> float:
    return 22 + min(104, max(0, x - 337) * 0.193)


def paint_opening(image: Image.Image) -> None:
    spill = Image.new("RGBA", image.size, (0, 0, 0, 0))
    spill_draw = ImageDraw.Draw(spill)
    spill_shape = [(337, -51), (875, -158), (1240, -158),
                   (1240, 158), (875, 158), (337, 51)]
    spill_draw.polygon(mapped(spill_shape), fill=(255, 101, 69, 160))
    image.alpha_composite(spill.filter(ImageFilter.GaussianBlur(36 * UPSCALE)))

    draw = ImageDraw.Draw(image, "RGBA")
    polygon_local(draw, [
        (337, -opening_width(337)), (875, -opening_width(875)), (1240, -126),
        (1240, 126), (875, opening_width(875)), (337, opening_width(337)),
    ], (238, 91, 83, 255))

    stops = [
        (-1.0, (255, 239, 165)), (-0.58, (255, 190, 82)),
        (-0.12, (255, 128, 66)), (0.34, (239, 85, 91)),
        (1.0, (103, 42, 104)),
    ]
    for (start, first), (finish, second) in zip(stops, stops[1:]):
        for step in range(18):
            low = start + (finish - start) * step / 18
            high = start + (finish - start) * (step + 1) / 18
            color = blend(first, second, (step + 0.5) / 18)
            polygon_local(draw, [
                (337, low * opening_width(337)), (875, low * opening_width(875)),
                (1240, low * 126), (1240, high * 126),
                (875, high * opening_width(875)), (337, high * opening_width(337)),
            ], (*color, 255))

    sun = zipper_point(782, 0)
    soft_glow(image, sun, 128, (255, 179, 74), 190, 28)
    draw = ImageDraw.Draw(image, "RGBA")
    cx, cy = to_canvas(sun)
    radius = 70 * UPSCALE
    for step in range(16, 0, -1):
        r = round(radius * step / 16)
        color = blend((255, 129, 71), (255, 246, 195), 1 - step / 20)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*color, 255))
    ring = 75 * UPSCALE
    draw.ellipse((cx - ring, cy - ring, cx + ring, cy + ring),
                 outline=(255, 247, 209, 220), width=3 * UPSCALE)
    line_local(draw, quadratic_curve((412, -75), (655, -126), (1090, -91)),
               (255, 237, 190, 165), 2)
    line_local(draw, quadratic_curve((414, 74), (655, 126), (1090, 91)),
               (255, 226, 177, 150), 2)
    line_local(draw, [(448, -32), (605, -52), (735, -41)],
               (255, 252, 219, 120), 1.5)


def zipper_tooth(x: float, gap: float, offset: float, upper: bool) -> list[Point]:
    if upper:
        edge = -gap - 19 - offset
        return [(x - 5, edge), (x + 5, edge), (x + 2.2, -gap), (x - 2.2, -gap)]
    edge = gap + 19 + offset
    return [(x - 5, edge), (x - 2.2, gap), (x + 2.2, gap), (x + 5, edge)]


def paint_tape(draw: ImageDraw.ImageDraw) -> None:
    for side in (-1, 1):
        polygon_local(draw, [
            (0, side * 47), (325, side * 47), (370, side * 23),
            (370, side * 43), (325, side * 63), (0, side * 63),
        ], (21, 93, 126, 255), (94, 218, 226, 255), 2)
        polygon_local(draw, [
            (366, side * 29), (1088, side * 133),
            (1088, side * 157), (366, side * 53),
        ], (21, 93, 126, 255), (94, 218, 226, 255), 2)
        line_local(draw, [(0, side * 55), (318, side * 55)], (109, 229, 230, 185), 2)
        line_local(draw, [(386, side * 41), (580, side * 121), (1090, side * 145)],
                   (192, 250, 238, 195), 2.2)
        for x in range(24, 320, 24):
            line_local(draw, [(x, side * 50), (x + 9, side * 60)],
                       (156, 227, 225, 86), 1)


def paint_slider(draw: ImageDraw.ImageDraw) -> None:
    polygon_local(draw, [
        (306, -36), (338, -51), (377, -31), (399, 0),
        (377, 31), (338, 51), (306, 36), (329, 0),
    ], (4, 17, 40, 180))
    polygon_local(draw, [
        (303, -34), (337, -48), (374, -30), (392, 0),
        (374, 30), (337, 48), (303, 34), (324, 0),
    ], (148, 188, 199, 255), (239, 249, 226, 255), 3)
    polygon_local(draw, [
        (311, -26), (337, -38), (360, -24), (377, 0),
        (360, 24), (337, 38), (311, 26), (330, 0),
    ], (24, 47, 74, 255), (118, 164, 184, 255), 3)
    line_local(draw, [(337, -39), (359, -27), (375, 0), (359, 27), (337, 39)],
               (251, 250, 220, 220), 3)
    for points in ([(310, -25), (328, -4)], [(310, 25), (328, 4)]):
        line_local(draw, points, (234, 247, 231, 225), 2)

    line_local(draw, [(310, 0), (281, 0)], (211, 181, 111, 255), 19)
    line_local(draw, [(310, 0), (281, 0)], (199, 218, 214, 255), 12)
    outer = [(284, -13), (280, -27), (263, -37), (242, -34), (226, -20),
             (218, -3), (223, 17), (240, 33), (261, 36), (279, 25), (287, 9)]
    line_local(draw, outer + [outer[0]], (249, 224, 161, 255), 20)
    line_local(draw, outer + [outer[0]], (147, 173, 182, 255), 12)
    inner = [(271, -7), (266, -17), (254, -20), (243, -14), (239, -2),
             (244, 11), (254, 16), (265, 12), (272, 3)]
    line_local(draw, inner + [inner[0]], (15, 29, 56, 255), 8)
    line_local(draw, [(229, -15), (238, -26), (252, -28)],
               (255, 250, 220, 230), 3)


def paint_teeth(draw: ImageDraw.ImageDraw) -> None:
    for index, x in enumerate(range(5, 1100, 15)):
        gap = 5 if x < 342 else min(126, 15 + (x - 342) * 0.205)
        offset = (index % 2) * 3
        for upper in (True, False):
            tooth = zipper_tooth(x, gap, offset, upper)
            polygon_local(draw, tooth, (110, 156, 177, 255), (13, 35, 60, 255), 1.5)
            if upper:
                shine = [(x - 4, tooth[0][1] + 2), (x - 1.7, tooth[0][1] + 2),
                         (x - 2.5, -gap - 5), (x - 4.2, -gap - 5)]
            else:
                shine = [(x + 1.5, gap + 5), (x + 3.8, gap + 5),
                         (x + 4, tooth[3][1] - 2), (x + 2, tooth[3][1] - 2)]
            polygon_local(draw, shine, (226, 241, 233, 235))


def paint_zipper(image: Image.Image) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    paint_tape(draw)
    paint_teeth(draw)
    paint_slider(draw)


def paint_witness(image: Image.Image) -> None:
    """Place a filled, dawn-lit traveler at the edge of the luminous seam."""
    draw = ImageDraw.Draw(image, "RGBA")
    draw.line([(706 * UPSCALE, 885 * UPSCALE), (920 * UPSCALE, 885 * UPSCALE)],
              fill=(76, 200, 211, 190), width=3 * UPSCALE)
    ink = (1, 5, 16, 255)
    cyan = (91, 220, 225, 255)
    amber = (255, 190, 109, 255)
    # The helmet is a solid dark shape with a bright horizon-facing rim.
    draw.ellipse((789 * UPSCALE, 811 * UPSCALE, 805 * UPSCALE, 827 * UPSCALE),
                 fill=ink, outline=amber, width=3 * UPSCALE)
    draw.arc((789 * UPSCALE, 811 * UPSCALE, 805 * UPSCALE, 827 * UPSCALE),
             start=205, end=335, fill=cyan, width=2 * UPSCALE)
    body = [
        (789, 829), (803, 828), (810, 843), (808, 856), (815, 878),
        (804, 880), (796, 859), (790, 878), (778, 876), (785, 853),
        (782, 839),
    ]
    silhouette = [(x * UPSCALE, y * UPSCALE) for x, y in body]
    draw.polygon(silhouette, fill=ink, outline=cyan, width=3 * UPSCALE)
    # A warm edge on the side facing the opening catches the sunrise.
    forward_rim = [(789, 832), (784, 841), (780, 850)]
    draw.line([(x * UPSCALE, y * UPSCALE) for x, y in forward_rim],
              fill=amber, width=2 * UPSCALE)
    for arm in (
        [(787, 836), (777, 847), (764, 853)],
        [(804, 835), (813, 841), (821, 844)],
    ):
        points = [(x * UPSCALE, y * UPSCALE) for x, y in arm]
        draw.line(points, fill=ink, width=7 * UPSCALE)
        draw.line(points, fill=cyan, width=2 * UPSCALE)
    draw.line([(775 * UPSCALE, 879 * UPSCALE), (769 * UPSCALE, 883 * UPSCALE)],
              fill=amber, width=3 * UPSCALE)
    draw.line([(807 * UPSCALE, 882 * UPSCALE), (815 * UPSCALE, 886 * UPSCALE)],
              fill=amber, width=3 * UPSCALE)


def render() -> None:
    canvas = paint_sky()
    paint_opening(canvas)
    paint_zipper(canvas)
    paint_witness(canvas)
    finished = canvas.convert("RGB").resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    finished.save(OUTPUT, format="PNG", optimize=True, compress_level=9)


if __name__ == "__main__":
    render()
