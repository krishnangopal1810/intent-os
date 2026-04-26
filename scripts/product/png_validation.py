#!/usr/bin/env python3
"""Dependency-free PNG content checks for UI evidence."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import struct
import zlib


CHANNELS_BY_COLOR_TYPE = {
    0: 1,
    2: 3,
    4: 2,
    6: 4,
}


def _paeth(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    left_distance = abs(estimate - left)
    up_distance = abs(estimate - up)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= up_distance and left_distance <= upper_left_distance:
        return left
    if up_distance <= upper_left_distance:
        return up
    return upper_left


def _read_chunks(data: bytes) -> tuple[dict[str, int], bytes]:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not a PNG")

    offset = 8
    idat_parts: list[bytes] = []
    ihdr: dict[str, int] | None = None

    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError("truncated PNG chunk header")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + length]
        offset += 12 + length

        if chunk_type == b"IHDR":
            if len(chunk_data) != 13:
                raise ValueError("invalid IHDR chunk")
            width, height, bit_depth, color_type, compression, filter_method, interlace = (
                struct.unpack(">IIBBBBB", chunk_data)
            )
            ihdr = {
                "width": width,
                "height": height,
                "bit_depth": bit_depth,
                "color_type": color_type,
                "compression": compression,
                "filter_method": filter_method,
                "interlace": interlace,
            }
        elif chunk_type == b"IDAT":
            idat_parts.append(chunk_data)
        elif chunk_type == b"IEND":
            break

    if ihdr is None:
        raise ValueError("missing IHDR chunk")
    if not idat_parts:
        raise ValueError("missing IDAT chunk")
    return ihdr, b"".join(idat_parts)


def png_content_stats(path: Path, sample_limit: int = 200_000) -> dict[str, object]:
    data = path.read_bytes()
    ihdr, compressed = _read_chunks(data)
    width = ihdr["width"]
    height = ihdr["height"]
    bit_depth = ihdr["bit_depth"]
    color_type = ihdr["color_type"]

    if bit_depth != 8:
        raise ValueError(f"unsupported PNG bit depth: {bit_depth}")
    if color_type not in CHANNELS_BY_COLOR_TYPE:
        raise ValueError(f"unsupported PNG color type: {color_type}")
    if ihdr["compression"] != 0 or ihdr["filter_method"] != 0 or ihdr["interlace"] != 0:
        raise ValueError("unsupported PNG encoding")

    channels = CHANNELS_BY_COLOR_TYPE[color_type]
    row_stride = width * channels
    raw = zlib.decompress(compressed)
    expected = height * (row_stride + 1)
    if len(raw) < expected:
        raise ValueError("truncated PNG pixel data")

    sample_step = max(1, (width * height) // sample_limit)
    colors: Counter[tuple[int, int, int]] = Counter()
    min_luma = 255
    max_luma = 0
    samples = 0
    previous = bytearray(row_stride)

    for y in range(height):
        row_offset = y * (row_stride + 1)
        filter_type = raw[row_offset]
        row = bytearray(raw[row_offset + 1 : row_offset + 1 + row_stride])
        for index in range(row_stride):
            left = row[index - channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 1:
                row[index] = (row[index] + left) & 0xFF
            elif filter_type == 2:
                row[index] = (row[index] + up) & 0xFF
            elif filter_type == 3:
                row[index] = (row[index] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                row[index] = (row[index] + _paeth(left, up, upper_left)) & 0xFF
            elif filter_type != 0:
                raise ValueError(f"unsupported PNG filter: {filter_type}")

        for x in range(0, width, sample_step):
            pixel_offset = x * channels
            if color_type == 0:
                red = green = blue = row[pixel_offset]
            elif color_type == 4:
                red = green = blue = row[pixel_offset]
            else:
                red, green, blue = row[pixel_offset : pixel_offset + 3]
            colors[(red, green, blue)] += 1
            luma = int((red * 299 + green * 587 + blue * 114) / 1000)
            min_luma = min(min_luma, luma)
            max_luma = max(max_luma, luma)
            samples += 1
        previous = row

    dominant = colors.most_common(1)[0][1] / samples if samples else 1
    return {
        "width": width,
        "height": height,
        "bytes": len(data),
        "sample_count": samples,
        "unique_color_count": len(colors),
        "luminance_range": max_luma - min_luma,
        "dominant_color_ratio": round(dominant, 4),
    }


def assert_useful_png(
    path: Path,
    *,
    min_width: int,
    min_height: int,
    min_unique_colors: int = 16,
    min_luminance_range: int = 16,
    max_dominant_color_ratio: float = 0.98,
) -> dict[str, object]:
    if not path.is_file():
        raise AssertionError(f"missing PNG {path}")
    stats = png_content_stats(path)
    if stats["width"] < min_width or stats["height"] < min_height:
        raise AssertionError(
            f"{path} dimensions are too small: {stats['width']}x{stats['height']}"
        )
    if stats["unique_color_count"] < min_unique_colors:
        raise AssertionError(f"{path} appears blank: only {stats['unique_color_count']} colors")
    if stats["luminance_range"] < min_luminance_range:
        raise AssertionError(f"{path} has too little contrast: {stats['luminance_range']}")
    if stats["dominant_color_ratio"] > max_dominant_color_ratio:
        raise AssertionError(
            f"{path} is dominated by one color: {stats['dominant_color_ratio']}"
        )
    return stats
