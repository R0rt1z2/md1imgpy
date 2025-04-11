"""
SPDX-FileCopyrightText: 2025 Roger Ortiz <me@r0rt1z2.com>
SPDX-License-Identifier: GPL-3.0-or-later
"""

from __future__ import annotations

import ctypes
from typing import Dict, Union

from md1imgpy.exceptions import HeaderError

MD1IMG_MAGIC1 = 0x58881688
MD1IMG_MAGIC2 = 0x58891689

GZ_HEADER = 0x1F8B
XZ_HEADER = 0xFD377A585A00

FILE_MAP_MARKER = b'md1_file_map'


class Md1Header(ctypes.Structure):
    """
    C-style structure representing the MD1 header.
    """

    _pack_ = 1
    _fields_ = [
        ('magic1', ctypes.c_uint32),  # 4 bytes
        ('data_size', ctypes.c_uint32),  # 4 bytes
        ('name', ctypes.c_char * 32),  # 32 bytes
        ('base', ctypes.c_uint32),  # 4 bytes
        ('mode', ctypes.c_uint32),  # 4 bytes
        ('magic2', ctypes.c_uint32),  # 4 bytes
        ('data_offset', ctypes.c_uint32),  # 4 bytes
        ('hdr_version', ctypes.c_uint32),  # 4 bytes
        ('img_type', ctypes.c_uint32),  # 4 bytes
        ('img_list_end', ctypes.c_uint32),  # 4 bytes
        ('align_size', ctypes.c_uint32),  # 4 bytes
        ('dsize_extend', ctypes.c_uint32),  # 4 bytes
        ('maddr_extend', ctypes.c_uint32),  # 4 bytes
        ('reserved', ctypes.c_uint8 * 432),  # 432 bytes (filled with 0xFF)
    ]

    @classmethod
    def from_bytes(cls, data: bytes) -> Md1Header:
        """
        Create a header from raw bytes.

        Args:
            data: Raw header data as bytes

        Returns:
            Md1Header instance

        Raises:
            HeaderError: If data is too small or invalid
        """
        if len(data) < ctypes.sizeof(cls):
            raise HeaderError(f'Header data too small: {len(data)} bytes')

        header = cls.from_buffer_copy(data)

        if header.magic1 != MD1IMG_MAGIC1 or header.magic2 != MD1IMG_MAGIC2:
            raise HeaderError('Invalid magic numbers in header')

        return header

    def to_bytes(self) -> bytes:
        """
        Convert header to bytes.

        Returns:
            Header as bytes
        """
        return bytes(self)

    def to_dict(self) -> Dict[str, Union[int, str]]:
        """
        Convert header to dictionary.

        Returns:
            Dictionary containing header fields
        """
        return {
            'magic1': f'0x{self.magic1:08x}',
            'data_size': self.data_size,
            'name': self.name.decode('utf-8', errors='ignore').rstrip('\x00'),
            'base': f'0x{self.base:08x}',
            'mode': f'0x{self.mode:08x}',
            'magic2': f'0x{self.magic2:08x}',
            'data_offset': f'0x{self.data_offset:08x}',
            'hdr_version': f'0x{self.hdr_version:08x}',
            'img_type': f'0x{self.img_type:08x}',
            'img_list_end': f'0x{self.img_list_end:08x}',
            'align_size': f'0x{self.align_size:08x}',
            'dsize_extend': f'0x{self.dsize_extend:08x}',
            'maddr_extend': f'0x{self.maddr_extend:08x}',
        }

    @classmethod
    def create(cls, name: str, data_size: int, base: int = 0) -> Md1Header:
        """
        Create a new header with default values.

        Args:
            name: Name of the file
            data_size: Size of the file data
            base: Base address (optional)

        Returns:
            New Md1Header instance
        """
        header = cls()
        header.magic1 = MD1IMG_MAGIC1
        header.data_size = data_size

        name_bytes = name.encode('utf-8')
        if len(name_bytes) > 31:
            name_bytes = name_bytes[:31]

        header.name = name_bytes
        header.base = base
        header.mode = 0
        header.magic2 = MD1IMG_MAGIC2
        header.data_offset = ctypes.sizeof(cls)
        header.hdr_version = 0
        header.img_type = 0
        header.img_list_end = 0
        header.align_size = 0
        header.dsize_extend = 0
        header.maddr_extend = 0

        for i in range(len(header.reserved)):
            header.reserved[i] = 0xFF

        return header

    def __str__(self) -> str:
        """
        String representation of the header.

        Returns:
            Formatted string with header information
        """
        info = self.to_dict()
        result = []
        for key, value in info.items():
            result.append(f'{key.ljust(15)}: {value}')
        return '\n'.join(result)


def is_gz_format(data: bytes) -> bool:
    """
    Check if data has a gzip header.

    Args:
        data: Data to check

    Returns:
        True if data has gzip header, False otherwise
    """
    if len(data) < 2:
        return False

    return data[0] == 0x1F and data[1] == 0x8B


def is_xz_format(data: bytes) -> bool:
    """
    Check if data has an XZ header.

    Args:
        data: Data to check

    Returns:
        True if data has XZ header, False otherwise
    """
    if len(data) < 6:
        return False

    return (
        data[0] == 0xFD
        and data[1] == 0x37
        and data[2] == 0x7A
        and data[3] == 0x58
        and data[4] == 0x5A
        and data[5] == 0x00
    )
