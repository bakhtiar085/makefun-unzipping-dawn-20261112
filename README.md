# Unzipping Dawn

An immense zipper opens the night sky into a molten sunrise. A lone traveler
stands at the seam, turning an everyday object into a doorway between worlds.
The artwork is an original procedural illustration.

## Offline entry

Python 3.13 and its standard library are sufficient:

```sh
MAKEFUN_OUTPUT_DIR=out /home/ubuntu/.local/bin/python3.13 main.py
```

The output directory defaults to `/output`. The program copies the committed
`entry.png` byte for byte.

## Development

`render_art.py` redraws the image and requires Pillow, which is only needed for
development. Run it with `python render_art.py`.

## Checks run

- Rendered `entry.png` with the development renderer and inspected the
  full-size result.
- Ran `main.py` twice with Python 3.13.15 from `/tmp`, with only `PATH` and
  `MAKEFUN_OUTPUT_DIR` set and separate temporary output directories. Both
  output SHA-256 hashes matched the committed image.
- Checked the PNG signature, terminal IEND chunk, 1024×1024 dimensions, and
  358,383-byte size.
