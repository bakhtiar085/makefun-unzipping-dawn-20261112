#!/usr/bin/env python3
"""Copy the finished artwork into the directory used by the competition."""

from __future__ import annotations

import os
from pathlib import Path


ARTWORK_NAME = "entry.png"
DEFAULT_OUTPUT = Path("/output")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_IEND = b"\x00\x00\x00\x00IEND\xaeB`\x82"
MAX_PNG_BYTES = 1_048_576


def output_directory() -> Path:
    """Return the requested output directory, or the competition default."""
    configured = os.environ.get("MAKEFUN_OUTPUT_DIR")
    return Path(configured) if configured else DEFAULT_OUTPUT


def copy_artwork() -> Path:
    """Create the output directory and copy the committed PNG byte for byte."""
    source = Path(__file__).resolve().with_name(ARTWORK_NAME)
    image = source.read_bytes()
    if len(image) > MAX_PNG_BYTES:
        raise ValueError(f"{ARTWORK_NAME} exceeds the 1 MiB limit")
    if not image.startswith(PNG_SIGNATURE) or not image.endswith(PNG_IEND):
        raise ValueError(f"{ARTWORK_NAME} is not a complete PNG")

    destination_dir = output_directory()
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / ARTWORK_NAME
    destination.write_bytes(image)
    return destination


def main() -> None:
    copy_artwork()


if __name__ == "__main__":
    main()
