import pytest

from sitegen.images import ImageError, image_size


def write(tmp_path, data):
    path = tmp_path / "image"
    path.write_bytes(data)
    return path


def riff(chunk: bytes, payload: bytes) -> bytes:
    return b"RIFF" + bytes(4) + b"WEBP" + chunk + bytes(4) + payload


def test_png(tmp_path):
    data = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + (1200).to_bytes(4, "big") + (630).to_bytes(4, "big")
    assert image_size(write(tmp_path, data)) == (1200, 630)


def test_webp_lossy(tmp_path):
    # VP8: 3 byte di frame tag + start code, poi larghezza e altezza a 14 bit
    payload = bytes(3) + b"\x9d\x01\x2a" + (800).to_bytes(2, "little") + (450).to_bytes(2, "little")
    assert image_size(write(tmp_path, riff(b"VP8 ", payload))) == (800, 450)


def test_webp_lossless(tmp_path):
    bits = (800 - 1) | ((450 - 1) << 14)
    payload = b"\x2f" + bits.to_bytes(4, "little")
    assert image_size(write(tmp_path, riff(b"VP8L", payload))) == (800, 450)


def test_webp_extended(tmp_path):
    payload = bytes(4) + (1600 - 1).to_bytes(3, "little") + (900 - 1).to_bytes(3, "little")
    assert image_size(write(tmp_path, riff(b"VP8X", payload))) == (1600, 900)


def test_unsupported_format(tmp_path):
    with pytest.raises(ImageError, match="unsupported"):
        image_size(write(tmp_path, b"\xff\xd8\xff" + bytes(30)))


def test_svg(tmp_path):
    path = tmp_path / "chart.svg"
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 420" width="800" height="420"></svg>')
    assert image_size(path) == (800, 420)


def test_svg_without_size_fails(tmp_path):
    path = tmp_path / "chart.svg"
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 420"></svg>')
    with pytest.raises(ImageError, match="width and height"):
        image_size(path)
