"""Dimensioni delle immagini, lette dall'intestazione del file (senza Pillow).

Servono per scrivere `width` e `height` negli <img>: il browser riserva lo
spazio giusto prima di scaricare l'immagine e la pagina non "salta".
Formati supportati: WebP e PNG (foto, screenshot), SVG (grafici).
"""

import re
import struct
from pathlib import Path


class ImageError(Exception):
    """Formato non supportato o file illeggibile."""


def image_size(path: Path) -> tuple[int, int]:
    """(larghezza, altezza) in pixel di un file WebP o PNG."""
    with path.open("rb") as f:
        head = f.read(32)

    # PNG: firma di 8 byte, poi il chunk IHDR con larghezza e altezza (big endian)
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return struct.unpack(">II", head[16:24])

    # WebP: contenitore RIFF; il formato del primo chunk dice dove sono le dimensioni
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        chunk = head[12:16]
        if chunk == b"VP8 ":  # lossy: due interi a 14 bit
            width, height = struct.unpack("<HH", head[26:30])
            return width & 0x3FFF, height & 0x3FFF
        if chunk == b"VP8L":  # lossless: 14 + 14 bit, meno uno
            bits = int.from_bytes(head[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if chunk == b"VP8X":  # esteso (trasparenza, animazione): 24 + 24 bit, meno uno
            return int.from_bytes(head[24:27], "little") + 1, int.from_bytes(head[27:30], "little") + 1

    # SVG: attributi width e height dell'elemento <svg> (in pixel, senza unità)
    if path.suffix == ".svg":
        root = re.search(r"<svg\b[^>]*>", path.read_text(encoding="utf-8"))
        width = root and re.search(r'\swidth="(\d+)"', root.group(0))
        height = root and re.search(r'\sheight="(\d+)"', root.group(0))
        if width and height:
            return int(width.group(1)), int(height.group(1))
        raise ImageError(f"{path}: the <svg> element needs width and height in pixels")

    raise ImageError(f"{path}: unsupported image format (use WebP, PNG or SVG)")
