#!/usr/bin/env python3
"""Render the public quickstart walkthrough as a deterministic animated GIF."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "assets" / "quickstart-demo.gif"
WIDTH, HEIGHT = 1280, 720

NAVY = "#08172f"
PANEL = "#102646"
PANEL_EDGE = "#31557f"
WHITE = "#f8fafc"
MUTED = "#a8bdd8"
BLUE = "#66aaff"
GREEN = "#4df0b0"
AMBER = "#ffbf32"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


TITLE = font(r"C:\Windows\Fonts\segoeuib.ttf", 46)
SUBTITLE = font(r"C:\Windows\Fonts\segoeui.ttf", 24)
MONO = font(r"C:\Windows\Fonts\CascadiaMono.ttf", 25)
MONO_BOLD = font(r"C:\Windows\Fonts\CascadiaMono.ttf", 27)
SMALL = font(r"C:\Windows\Fonts\segoeui.ttf", 20)


STAGES = [
    [
        (GREEN, "$ git clone https://github.com/fusiontechstrategies/AI-Accuracy-Harness.git"),
        (GREEN, "$ cd AI-Accuracy-Harness"),
    ],
    [
        (GREEN, "$ python -m unittest discover -s tests"),
        (MUTED, ".................."),
        (WHITE, "Ran 18 tests"),
        (GREEN, "OK"),
    ],
    [
        (GREEN, "$ python tools/verify_package.py"),
        (GREEN, "PACKAGE VERIFIED: 57 payload files"),
        (MUTED, "MANIFEST SHA256: checksum validated"),
    ],
    [
        (GREEN, "$ python select_lane.py examples/remote-bounded-routing-request.json"),
        (BLUE, '"lane": "OPENROUTER_CEREBRAS_GPT_OSS_120B"'),
        (GREEN, '"admission": "ADMITTED_PROPOSAL_ONLY"'),
    ],
    [
        (GREEN, '"admission": "ADMITTED_PROPOSAL_ONLY"'),
        (AMBER, '"tools_allowed": false'),
        (AMBER, '"repository_mutation_allowed": false'),
        (AMBER, '"semantic_approval": false'),
    ],
]


def frame(lines: list[tuple[str, str]], step: int) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((55, 45, WIDTH - 55, HEIGHT - 45), radius=30, fill=PANEL, outline=PANEL_EDGE, width=3)
    draw.ellipse((88, 78, 108, 98), fill="#ff6b6b")
    draw.ellipse((120, 78, 140, 98), fill=AMBER)
    draw.ellipse((152, 78, 172, 98), fill=GREEN)

    draw.text((88, 135), "AI Accuracy Harness", font=TITLE, fill=WHITE)
    draw.text((90, 198), "A 60-second evidence check", font=SUBTITLE, fill=MUTED)

    y = 278
    for color, value in lines:
        draw.text((92, y), value, font=MONO, fill=color)
        y += 52

    draw.line((90, HEIGHT - 104, WIDTH - 90, HEIGHT - 104), fill=PANEL_EDGE, width=2)
    draw.text((92, HEIGHT - 84), "Evidence first", font=SMALL, fill=GREEN)
    draw.text((260, HEIGHT - 84), "|", font=SMALL, fill=PANEL_EDGE)
    draw.text((286, HEIGHT - 84), "Proposal only", font=SMALL, fill=AMBER)
    draw.text((WIDTH - 188, HEIGHT - 84), f"{step}/5", font=MONO_BOLD, fill=BLUE)
    return image


def main() -> None:
    frames = [frame(lines, index) for index, lines in enumerate(STAGES, start=1)]
    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=[1250, 1500, 1700, 1700, 2600],
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"WROTE {OUTPUT} ({OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
