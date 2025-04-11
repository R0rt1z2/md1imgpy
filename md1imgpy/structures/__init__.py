"""
SPDX-FileCopyrightText: 2025 Roger Ortiz <me@r0rt1z2.com>
SPDX-License-Identifier: GPL-3.0-or-later
"""

from md1imgpy.structures.header import (
    FILE_MAP_MARKER,
    GZ_HEADER,
    MD1IMG_MAGIC1,
    MD1IMG_MAGIC2,
    XZ_HEADER,
    Md1Header,
    is_gz_format,
    is_xz_format,
)

__all__ = [
    'Md1Header',
    'MD1IMG_MAGIC1',
    'MD1IMG_MAGIC2',
    'GZ_HEADER',
    'XZ_HEADER',
    'FILE_MAP_MARKER',
    'is_gz_format',
    'is_xz_format',
]
