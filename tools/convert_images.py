#!/usr/bin/env python3
"""
Converts truecolor RGBA PNG files into indexed PNG files with a transparency
(tRNS) chunk so they display correctly with the displayio graphics driver.

WHY?

On microcontrollers, images are loaded with adafruit_imageload which discards
the alpha channel of truecolor (RGBA) PNG files. The displayio graphics driver
then falls back to colour key transparency with black as the key, so any
genuinely black pixels in the artwork become transparent (see LIMITATION:
TRANSPARENCY in pmpge/drivers/graphics/displayio.py).

Indexed PNG files with a tRNS chunk do not have this problem: the transparent
pixels get their own palette entry (index 0), separate from every opaque
colour - including opaque black. adafruit_imageload applies the tRNS
transparency itself and the graphics driver leaves such images untouched.
Pygame Zero loads them natively, so a converted image displays identically on
desktop and on a microcontroller. Indexed images also load faster and use
less RAM on a microcontroller than truecolor images.

Pixels with an alpha value below the threshold (default 128) become fully
transparent; all other pixels become fully opaque. Partial transparency
cannot be represented with a colour key.

This script only uses the Python standard library (no Pillow required).

USAGE

    # Convert files in place (files that are already indexed are skipped)
    python tools/convert_images.py image.png my_game/images

    # Convert into a separate directory instead of in place
    python tools/convert_images.py my_game/images --out-dir converted
"""

import argparse
import os
import shutil
import struct
import sys
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# The colour stored in the reserved transparent palette entry (index 0). It is
# never visible when transparency works, so a garish colour is used to make it
# obvious if the image is ever displayed without transparency enabled.
TRANSPARENT_COLOUR = (255, 0, 255)


class ConversionError(Exception):
    """Raised when a PNG file cannot be converted."""


class SkipImage(Exception):
    """Raised when a PNG file does not need converting."""


def read_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    """Splits a PNG file into its chunks, returned as (type, payload) pairs."""
    if data[:8] != PNG_SIGNATURE:
        raise ConversionError("not a PNG file")

    chunks = []
    position = 8
    while position < len(data):
        (length,) = struct.unpack(">I", data[position:position + 4])
        chunks.append((data[position + 4:position + 8], data[position + 8:position + 8 + length]))
        position += 12 + length

    return chunks


def write_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    """Encodes a single PNG chunk, including its length and CRC."""
    crc = zlib.crc32(chunk_type + payload)
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc)


def reverse_sub_filter(line: bytearray, _, bytes_per_pixel: int):
    for x in range(bytes_per_pixel, len(line)):
        line[x] = (line[x] + line[x - bytes_per_pixel]) & 255


def reverse_up_filter(line: bytearray, previous: bytearray, _):
    for x in range(len(line)):
        line[x] = (line[x] + previous[x]) & 255


def reverse_average_filter(line: bytearray, previous: bytearray, bytes_per_pixel: int):
    for x in range(len(line)):
        left = line[x - bytes_per_pixel] if x >= bytes_per_pixel else 0
        line[x] = (line[x] + (left + previous[x]) // 2) & 255


def reverse_paeth_filter(line: bytearray, previous: bytearray, bytes_per_pixel: int):
    for x in range(len(line)):
        left = line[x - bytes_per_pixel] if x >= bytes_per_pixel else 0
        up = previous[x]
        up_left = previous[x - bytes_per_pixel] if x >= bytes_per_pixel else 0

        distance_left = abs(up - up_left)
        distance_up = abs(left - up_left)
        distance_up_left = abs(left + up - 2 * up_left)
        if distance_left <= distance_up and distance_left <= distance_up_left:
            predictor = left
        elif distance_up <= distance_up_left:
            predictor = up
        else:
            predictor = up_left

        line[x] = (line[x] + predictor) & 255


FILTER_REVERSERS = {1: reverse_sub_filter, 2: reverse_up_filter, 3: reverse_average_filter, 4: reverse_paeth_filter}


def unfilter_scanlines(raw: bytes, width: int, height: int, bytes_per_pixel: int) -> bytearray:
    """Reverses the per-scanline PNG filters, returning the raw pixel bytes."""
    stride = width * bytes_per_pixel
    pixels = bytearray()
    previous = bytearray(stride)

    position = 0
    for _ in range(height):
        filter_type = raw[position]
        line = bytearray(raw[position + 1:position + 1 + stride])
        position += 1 + stride

        if filter_type != 0:
            if filter_type not in FILTER_REVERSERS:
                raise ConversionError(f"unsupported PNG filter type {filter_type}")
            FILTER_REVERSERS[filter_type](line, previous, bytes_per_pixel)

        pixels.extend(line)
        previous = line

    return pixels


def read_rgba_png(data: bytes) -> tuple[int, int, bytearray]:
    """
    Decodes an 8 bit per channel truecolor PNG with alpha, returning the width,
    height and a flat RGBA bytearray. Raises SkipImage for PNG files that do not
    need converting and ConversionError for those that cannot be converted.
    """
    chunks = read_chunks(data)
    if not chunks or chunks[0][0] != b"IHDR":
        raise ConversionError("missing IHDR chunk")

    width, height, bit_depth, colour_type, _, _, interlace = struct.unpack(">IIBBBBB", chunks[0][1])

    if colour_type == 3:
        raise SkipImage("already an indexed PNG")
    if colour_type == 2:
        raise SkipImage("truecolor PNG without an alpha channel; nothing is transparent")
    if colour_type != 6:
        raise ConversionError(f"unsupported PNG colour type {colour_type}")
    if bit_depth != 8:
        raise ConversionError(f"unsupported bit depth {bit_depth} (only 8 bits per channel is supported)")
    if interlace != 0:
        raise ConversionError("interlaced PNG files are not supported")

    compressed = b"".join(payload for chunk_type, payload in chunks if chunk_type == b"IDAT")
    return width, height, unfilter_scanlines(zlib.decompress(compressed), width, height, 4)


def build_indexed_pixels(pixels: bytearray, alpha_threshold: int) -> tuple[bytearray, list[tuple[int, int, int]]]:
    """
    Maps each RGBA pixel to a palette index. Index 0 is reserved for transparent
    pixels; opaque colours are added to the palette in the order they first appear.
    """
    palette = [TRANSPARENT_COLOUR]
    colour_to_index = {}
    indices = bytearray()

    for position in range(0, len(pixels), 4):
        red, green, blue, alpha = pixels[position:position + 4]
        if alpha < alpha_threshold:
            indices.append(0)
            continue

        colour = (red, green, blue)
        index = colour_to_index.get(colour)
        if index is None:
            if len(palette) > 255:
                raise ConversionError("more than 255 opaque colours; reduce the number of colours in the image")
            index = len(palette)
            colour_to_index[colour] = index
            palette.append(colour)

        indices.append(index)

    return indices, palette


def choose_bit_depth(palette_size: int) -> int:
    """Returns the smallest PNG bit depth that can hold the palette."""
    for bit_depth in (1, 2, 4):
        if palette_size <= 1 << bit_depth:
            return bit_depth
    return 8


def pack_scanlines(indices: bytearray, width: int, height: int, bit_depth: int) -> bytes:
    """Packs the palette indices into filter type 0 scanlines at the given bit depth."""
    pixels_per_byte = 8 // bit_depth
    packed = bytearray()

    for y in range(height):
        row = indices[y * width:(y + 1) * width]
        packed.append(0)  # Filter type 0 (None)
        for x in range(0, width, pixels_per_byte):
            byte = 0
            for offset, index in enumerate(row[x:x + pixels_per_byte]):
                byte |= index << (8 - bit_depth * (offset + 1))
            packed.append(byte)

    return bytes(packed)


def write_indexed_png(width: int, height: int, indices: bytearray, palette: list[tuple[int, int, int]]) -> bytes:
    """Encodes an indexed PNG in which palette index 0 is transparent (via a tRNS chunk)."""
    bit_depth = choose_bit_depth(len(palette))
    header = struct.pack(">IIBBBBB", width, height, bit_depth, 3, 0, 0, 0)
    idat = zlib.compress(pack_scanlines(indices, width, height, bit_depth), 9)

    return (PNG_SIGNATURE
            + write_chunk(b"IHDR", header)
            + write_chunk(b"PLTE", b"".join(bytes(colour) for colour in palette))
            + write_chunk(b"tRNS", b"\x00")
            + write_chunk(b"IDAT", idat)
            + write_chunk(b"IEND", b""))


def convert(data: bytes, alpha_threshold: int = 128) -> bytes:
    """Converts a truecolor RGBA PNG into an indexed PNG with a tRNS chunk."""
    width, height, pixels = read_rgba_png(data)
    indices, palette = build_indexed_pixels(pixels, alpha_threshold)
    return write_indexed_png(width, height, indices, palette)


def read_indexed_png(data: bytes) -> tuple[int, int, bytearray, list[tuple[int, int, int]], bytes]:
    """
    Decodes an indexed PNG as written by this script (filter type 0 scanlines only),
    returning the width, height, palette indices, palette and raw tRNS payload.
    Used to verify conversions and by the unit tests.
    """
    chunks = read_chunks(data)
    width, height, bit_depth, colour_type, _, _, interlace = struct.unpack(">IIBBBBB", chunks[0][1])
    if colour_type != 3 or interlace != 0:
        raise ConversionError("not a non-interlaced indexed PNG")

    plte = next(payload for chunk_type, payload in chunks if chunk_type == b"PLTE")
    palette = [tuple(plte[i:i + 3]) for i in range(0, len(plte), 3)]
    trns = next((payload for chunk_type, payload in chunks if chunk_type == b"tRNS"), b"")

    compressed = b"".join(payload for chunk_type, payload in chunks if chunk_type == b"IDAT")
    raw = zlib.decompress(compressed)

    pixels_per_byte = 8 // bit_depth
    stride = (width + pixels_per_byte - 1) // pixels_per_byte
    mask = (1 << bit_depth) - 1

    indices = bytearray()
    for y in range(height):
        if raw[y * (stride + 1)] != 0:
            raise ConversionError("only filter type 0 scanlines are supported")
        row = raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)]
        for x in range(width):
            shift = 8 - bit_depth * (x % pixels_per_byte + 1)
            indices.append((row[x // pixels_per_byte] >> shift) & mask)

    return width, height, indices, palette, trns


def collect_png_files(paths: list[str]) -> list[tuple[str, str]]:
    """Expands the given files and directories into (path, relative name) pairs."""
    files = []
    for path in paths:
        if os.path.isdir(path):
            for directory, _, names in os.walk(path):
                for name in sorted(names):
                    if name.lower().endswith(".png"):
                        full = os.path.join(directory, name)
                        files.append((full, os.path.relpath(full, path)))
        else:
            files.append((path, os.path.basename(path)))

    return files


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert RGBA PNG files into indexed PNG files with a tRNS chunk "
                    "for correct transparency with the displayio graphics driver.")
    parser.add_argument("paths", nargs="+", help="PNG files or directories of PNG files to convert")
    parser.add_argument("--out-dir", help="write converted files here instead of converting in place")
    parser.add_argument("--threshold", type=int, default=128,
                        help="alpha values below this become transparent (default 128)")
    options = parser.parse_args(arguments)

    for path in options.paths:
        if not os.path.exists(path):
            parser.error(f"{path}: no such file or directory")

    failures = 0
    for source, relative in collect_png_files(options.paths):
        destination = os.path.join(options.out_dir, relative) if options.out_dir else source
        try:
            with open(source, "rb") as file:
                converted = convert(file.read(), options.threshold)

            os.makedirs(os.path.dirname(destination) or ".", exist_ok=True)
            with open(destination, "wb") as file:
                file.write(converted)
            print(f"converted {source} -> {destination}")

        except SkipImage as skip:
            # When writing to a separate directory, copy skipped files across so the
            # output directory always contains the complete set of images.
            if options.out_dir:
                os.makedirs(os.path.dirname(destination) or ".", exist_ok=True)
                shutil.copyfile(source, destination)
            print(f"skipped   {source}: {skip}")

        except (ConversionError, zlib.error) as error:
            print(f"FAILED    {source}: {error}")
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
