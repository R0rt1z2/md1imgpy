"""
SPDX-FileCopyrightText: 2025 Roger Ortiz <me@r0rt1z2.com>
SPDX-License-Identifier: GPL-3.0-or-later
"""

from __future__ import annotations

import ctypes
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Union

from md1imgpy.exceptions import HeaderError, InvalidIOFile
from md1imgpy.structures import (
    FILE_MAP_MARKER,
    Md1Header,
)

logger = logging.getLogger(__name__)


@dataclass
class Md1File:
    """
    Represents a file in the MD1 image.

    Attributes:
        name: Original name of the file
        header: MD1 header for this file
        data: Raw data of the file
        offset: Offset of the file in the image
    """

    name: str
    header: Md1Header
    data: bytes
    offset: int

    @property
    def size(self) -> int:
        """
        Get the size of the file data.

        Returns:
            Size in bytes
        """
        return len(self.data)

    def __str__(self) -> str:
        """
        String representation of the file.

        Returns:
            Formatted string with file information
        """
        return f'MD1File: {self.name} (size: {self.size} bytes, offset: 0x{self.offset:08x})\n{str(self.header)}'


class Md1Image:
    """
    Represents an MD1 image with methods to read and modify its contents.

    Attributes:
        path: Path to the image file
        files: List of files in the image
        file_mapping: Mapping from original filenames to external ones
        meta_info: Metadata for each file in the image
    """

    def __init__(self, image_path: Optional[Union[str, Path]] = None):
        """
        Initialize an MD1 image, optionally loading from a file.

        Args:
            image_path: Optional path to an MD1 image file to load

        Raises:
            InvalidIOFile: If the image file cannot be read
        """
        self.path = Path(image_path) if image_path else None
        self.files: List[Md1File] = []
        self.file_mapping: Dict[str, str] = {}
        self.meta_info: Dict[str, Dict[str, str]] = {}

        if self.path and self.path.exists():
            self._load_image()

    def _load_image(self) -> None:
        """
        Load the image file and parse its structure.

        Raises:
            InvalidIOFile: If the image file cannot be read
            HeaderError: If headers are invalid
        """
        if not self.path:
            return

        try:
            with open(self.path, 'rb') as f:
                self._find_file_mapping(f)

                f.seek(0)
                file_size = os.path.getsize(self.path)
                offset = 0

                while offset < file_size:
                    f.seek(offset)

                    header_data = f.read(ctypes.sizeof(Md1Header))
                    if not header_data or len(header_data) < ctypes.sizeof(
                        Md1Header
                    ):
                        break

                    try:
                        header = Md1Header.from_bytes(header_data)
                    except HeaderError:
                        break

                    name = header.name.decode('utf-8', errors='ignore').rstrip(
                        '\x00'
                    )
                    logger.debug(
                        f'Found file: {name} (size: {header.data_size} bytes, offset: 0x{offset:08x})'
                    )

                    f.seek(offset + header.data_offset)

                    data = f.read(header.data_size)
                    if len(data) != header.data_size:
                        logger.warning(
                            f'Truncated data for {name}: expected {header.data_size}, got {len(data)} bytes'
                        )

                    md1_file = Md1File(
                        name=name, header=header, data=data, offset=offset
                    )
                    self.files.append(md1_file)

                    offset += header.data_offset + header.data_size
                    if offset % 16 != 0:
                        offset += 16 - (offset % 16)

        except (OSError, IOError) as e:
            raise InvalidIOFile(f'Failed to load MD1 image: {e}', self.path)

    def _find_file_mapping(self, f: BinaryIO) -> None:
        """
        Find and parse the file mapping within the image.

        Args:
            f: Open file handle for the image

        Raises:
            MapFileNotFoundError: If mapping is not found and required
        """
        try:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()

            buffer_size = 16384
            marker = FILE_MAP_MARKER

            pos = file_size
            while pos > 0:
                chunk_size = min(buffer_size, pos)
                pos -= chunk_size
                f.seek(pos)
                buffer = f.read(chunk_size)

                marker_pos = buffer.rfind(marker)
                if marker_pos >= 0:
                    map_offset = pos + marker_pos
                    f.seek(map_offset + len(marker) + 504)
                    map_content = f.read().decode('utf-8', errors='ignore')
                    self._parse_file_mapping(map_content)
                    return

            logger.warning('No file mapping found in image')

        except (OSError, IOError) as e:
            logger.error(f'Error searching for file mapping: {e}')

    def _parse_file_mapping(self, content: str) -> None:
        """
        Parse file mapping content.

        Args:
            content: Text content of the mapping section
        """
        self.file_mapping = {}

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            parts = line.split('=', 1)
            if len(parts) != 2:
                continue

            key, value = parts
            self.file_mapping[key] = value

    def save(self, output_path: Union[str, Path]) -> None:
        """
        Save the MD1 image to a file.

        Args:
            output_path: Path where to save the image

        Raises:
            InvalidIOFile: If the file cannot be written
        """
        try:
            with open(output_path, 'wb') as f:
                for md1_file in self.files:
                    f.write(md1_file.header.to_bytes())

                    f.write(md1_file.data)

                    padding_size = 16 - (len(md1_file.data) % 16)
                    if padding_size != 16:
                        f.write(b'\x00' * padding_size)

            logger.info(f'Saved MD1 image to {output_path}')

        except (OSError, IOError) as e:
            raise InvalidIOFile(f'Failed to save MD1 image: {e}', output_path)

    def get_file_by_name(self, name: str) -> Optional[Md1File]:
        """
        Get a file from the image by its name.

        Args:
            name: Name of the file to get

        Returns:
            Md1File object if found, None otherwise
        """
        for md1_file in self.files:
            if md1_file.name == name:
                return md1_file
        return None

    def get_file_names(self) -> List[str]:
        """
        Get the names of all files in the image.

        Returns:
            List of file names
        """
        return [md1_file.name for md1_file in self.files]

    def add_file(self, name: str, data: bytes, base: int = 0) -> Md1File:
        """
        Add a new file to the image.

        Args:
            name: Name of the file
            data: File data
            base: Base address for the file

        Returns:
            The created Md1File object
        """
        header = Md1Header.create(name, len(data), base)

        offset = 0
        if self.files:
            last_file = self.files[-1]
            offset = (
                last_file.offset + last_file.header.data_offset + last_file.size
            )
            if offset % 16 != 0:
                offset += 16 - (offset % 16)

        md1_file = Md1File(name=name, header=header, data=data, offset=offset)
        self.files.append(md1_file)

        return md1_file

    def remove_file(self, name: str) -> bool:
        """
        Remove a file from the image.

        Args:
            name: Name of the file to remove

        Returns:
            True if file was removed, False if not found
        """
        for i, md1_file in enumerate(self.files):
            if md1_file.name == name:
                self.files.pop(i)
                return True
        return False

    @property
    def size(self) -> int:
        """
        Get the total size of the image.

        Returns:
            Size in bytes (estimated based on file contents)
        """
        total_size = 0
        for md1_file in self.files:
            file_size = md1_file.header.data_offset + md1_file.size
            if file_size % 16 != 0:
                file_size += 16 - (file_size % 16)
            total_size += file_size
        return total_size

    def __str__(self) -> str:
        """
        String representation of the image.

        Returns:
            Formatted string with image information
        """
        result = [
            f'MD1 Image: {self.path or "New image"} (size: {self.size} bytes)'
        ]
        result.append(f'Files: {len(self.files)}')

        for i, md1_file in enumerate(self.files, 1):
            mapped_name = 'Unknown'
            for original, mapped in self.file_mapping.items():
                if mapped == md1_file.name:
                    mapped_name = original
                    break

            result.append(
                f'{i}. {md1_file.name} -> {mapped_name} (size: {md1_file.size} bytes)'
            )

        return '\n'.join(result)
