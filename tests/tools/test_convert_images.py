import pathlib
import struct
import zlib

import pytest

from tools import convert_images
from tools.convert_images import ConversionError, SkipImage, convert, read_indexed_png, read_rgba_png

TRANSPARENT = (0, 0, 0, 0)
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
RED = (255, 0, 0, 255)


def make_rgba_png(width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> bytes:
    """Encodes a list of RGBA pixel tuples into a truecolor PNG with an alpha channel."""
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # Filter type 0 (None)
        for x in range(width):
            raw.extend(pixels[y * width + x])

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (convert_images.PNG_SIGNATURE
            + convert_images.write_chunk(b"IHDR", header)
            + convert_images.write_chunk(b"IDAT", zlib.compress(bytes(raw)))
            + convert_images.write_chunk(b"IEND", b""))


def decode_to_rgba(data: bytes) -> list[tuple[int, int, int, int]]:
    """Decodes an indexed PNG back into RGBA tuples, applying the tRNS transparency."""
    _, _, indices, palette, trns = read_indexed_png(data)
    return [palette[i] + ((trns[i] if i < len(trns) else 255),) for i in indices]


def test_opaque_black_is_distinct_from_transparency():
    # This is the original bug: an image containing both transparent pixels and
    # genuinely black pixels must keep the black pixels opaque.
    original = make_rgba_png(2, 2, [BLACK, TRANSPARENT, WHITE, BLACK])
    converted = convert(original)

    _, _, indices, palette, trns = read_indexed_png(converted)

    assert trns == b"\x00"  # Only palette index 0 is transparent
    assert indices[1] == 0  # The transparent pixel uses the reserved index
    assert indices[0] != 0 and indices[0] == indices[3]  # Opaque black pixels share another index
    assert palette[indices[0]] == (0, 0, 0)


def test_round_trip_preserves_visible_pixels():
    pixels = [BLACK, TRANSPARENT, WHITE, RED, (1, 2, 3, 255), (200, 100, 50, 255)]
    converted = convert(make_rgba_png(3, 2, pixels))

    assert decode_to_rgba(converted) == [(0, 0, 0, 255), (255, 0, 255, 0), (255, 255, 255, 255),
                                         (255, 0, 0, 255), (1, 2, 3, 255), (200, 100, 50, 255)]


def test_smallest_bit_depth_is_chosen():
    # Three opaque colours plus the transparent entry fit in 2 bits per pixel. Use a
    # width that is not a whole number of bytes to also exercise the row padding.
    pixels = [BLACK, WHITE, RED, TRANSPARENT, BLACK, WHITE, RED, TRANSPARENT, BLACK]
    converted = convert(make_rgba_png(3, 3, pixels))

    _, _, bit_depth, colour_type, _, _, _ = struct.unpack(">IIBBBBB", convert_images.read_chunks(converted)[0][1])
    assert (bit_depth, colour_type) == (2, 3)

    alpha = [p[3] for p in decode_to_rgba(converted)]
    assert alpha == [255, 255, 255, 0, 255, 255, 255, 0, 255]


def test_alpha_threshold():
    pixels = [(10, 20, 30, 100), (10, 20, 30, 200)]

    alpha = [p[3] for p in decode_to_rgba(convert(make_rgba_png(2, 1, pixels)))]
    assert alpha == [0, 255]

    alpha = [p[3] for p in decode_to_rgba(convert(make_rgba_png(2, 1, pixels), alpha_threshold=50))]
    assert alpha == [255, 255]


def test_at_most_255_opaque_colours():
    # 255 opaque colours (plus the reserved transparent entry) is the maximum.
    colours = [(r, g, 0, 255) for r in range(16) for g in range(16)]

    convert(make_rgba_png(16, 16, [TRANSPARENT] + colours[:255]))

    with pytest.raises(ConversionError):
        convert(make_rgba_png(16, 16, colours))


def test_indexed_and_opaque_truecolor_images_are_skipped():
    converted = convert(make_rgba_png(1, 1, [WHITE]))
    with pytest.raises(SkipImage):
        convert(converted)

    raw = bytes([0, 1, 2, 3])  # One filter type 0 scanline with a single RGB pixel
    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    opaque = (convert_images.PNG_SIGNATURE
              + convert_images.write_chunk(b"IHDR", header)
              + convert_images.write_chunk(b"IDAT", zlib.compress(raw))
              + convert_images.write_chunk(b"IEND", b""))
    with pytest.raises(SkipImage):
        convert(opaque)


def test_real_assets_round_trip():
    # Convert real engine assets (which contain transparency stored as black) and
    # check every pixel survives: transparent stays transparent, visible colours
    # - including opaque black - are unchanged.
    repo_root = pathlib.Path(__file__).parents[2]
    for asset in ["assets/images/space/earth.png", "assets/images/games/aliens/alien_a_1.png"]:
        with open(repo_root / asset, "rb") as file:
            original = file.read()

        width, height, pixels = read_rgba_png(original)
        converted = convert(original)
        result = decode_to_rgba(converted)

        for position in range(width * height):
            red, green, blue, alpha = pixels[position * 4:position * 4 + 4]
            if alpha < 128:
                assert result[position][3] == 0
            else:
                assert result[position] == (red, green, blue, 255)


def test_pygame_loads_converted_images():
    # Pygame (and therefore Pygame Zero on desktop) must be able to load the
    # converted files so the same image works on both platforms.
    pygame = pytest.importorskip("pygame")
    import io

    converted = convert(make_rgba_png(2, 2, [BLACK, TRANSPARENT, WHITE, RED]))
    surface = pygame.image.load(io.BytesIO(converted), "image.png")
    assert surface.get_size() == (2, 2)


def test_main_converts_in_place_and_to_out_dir(tmp_path):
    source_dir = tmp_path / "images"
    source_dir.mkdir()
    (source_dir / "sprite.png").write_bytes(make_rgba_png(2, 1, [BLACK, TRANSPARENT]))

    out_dir = tmp_path / "converted"
    assert convert_images.main([str(source_dir), "--out-dir", str(out_dir)]) == 0
    assert decode_to_rgba((out_dir / "sprite.png").read_bytes()) == [(0, 0, 0, 255), (255, 0, 255, 0)]

    # In place: the first run converts, the second run skips the now-indexed file.
    assert convert_images.main([str(source_dir)]) == 0
    assert convert_images.main([str(source_dir)]) == 0
    assert decode_to_rgba((source_dir / "sprite.png").read_bytes()) == [(0, 0, 0, 255), (255, 0, 255, 0)]
