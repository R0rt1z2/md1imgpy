"""
SPDX-FileCopyrightText: 2025 Roger Ortiz <me@r0rt1z2.com>
SPDX-License-Identifier: GPL-3.0-or-later
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from md1imgpy.config import CompressionFormat, Md1ImgConfig
from md1imgpy.exceptions import InvalidIOFile, Md1ImgError
from md1imgpy.image import Md1File, Md1Image
from md1imgpy.structures import Md1Header
from md1imgpy.utils import (
    compress_gz,
    compress_xz,
    extract_number,
    parse_meta_info,
    read_file_mapping,
    strip_number,
    to_lowercase,
)

logger = logging.getLogger(__name__)


class Md1Packer:
    """
    Packs files into an MD1 image.

    Provides functionality to create MD1 images from files,
    handling compression as needed.

    Attributes:
        config: Configuration for the packer
        files: List of files to pack
        file_mapping: Mapping from external filenames to MD1 names
        meta_info: Metadata for each file
    """

    def __init__(self, config: Optional[Md1ImgConfig] = None):
        """
        Initialize the packer.

        Args:
            config: Optional configuration settings
        """
        self.config = config or Md1ImgConfig()
        self.files: List[Path] = []
        self.file_mapping: Dict[str, str] = {}
        self.meta_info: Dict[str, Dict[str, str]] = {}

        logger.info('Initialized MD1 packer')

    def add_directory(self, directory: Union[str, Path]) -> None:
        """
        Add all files from a directory for packing.

        Args:
            directory: Directory containing files to pack

        Raises:
            InvalidIOFile: If directory doesn't exist or can't be read
        """
        directory_path = Path(directory)

        if not directory_path.exists() or not directory_path.is_dir():
            raise InvalidIOFile('Not a valid directory', directory_path)

        map_file_path = None
        meta_info_path = None

        for entry in directory_path.iterdir():
            if entry.is_file():
                if 'md1_file_map' in entry.name:
                    map_file_path = entry
                elif entry.name == 'meta_info':
                    meta_info_path = entry

        if map_file_path:
            try:
                with open(map_file_path, 'r') as f:
                    self.file_mapping = read_file_mapping(f.read())
                logger.info(f'Loaded file mapping from {map_file_path}')
            except (OSError, IOError) as e:
                logger.warning(f'Failed to read file mapping: {e}')

        if meta_info_path:
            try:
                with open(meta_info_path, 'r') as f:
                    self.meta_info = parse_meta_info(f.read())
                logger.info(f'Loaded meta_info from {meta_info_path}')
            except (OSError, IOError) as e:
                logger.warning(f'Failed to read meta_info: {e}')

        for entry in directory_path.iterdir():
            if entry.is_file() and entry.name != 'meta_info':
                self.files.append(entry)

        self.files.sort(key=lambda f: extract_number(f.name))

        logger.info(f'Added {len(self.files)} files from {directory}')

    def add_file(self, file_path: Union[str, Path]) -> None:
        """
        Add a single file for packing.

        Args:
            file_path: Path to the file to add

        Raises:
            InvalidIOFile: If file doesn't exist or can't be read
        """
        path = Path(file_path)

        if not path.exists() or not path.is_file():
            raise InvalidIOFile('Not a valid file', path)

        self.files.append(path)
        logger.info(f'Added file: {path}')

    def pack(self, output_path: Union[str, Path]) -> Path:
        """
        Pack files into an MD1 image.

        Args:
            output_path: Path where to save the image

        Returns:
            Path to the created image

        Raises:
            InvalidIOFile: If output file cannot be written
            Md1ImgError: If no files to pack
        """
        if not self.files:
            raise Md1ImgError('No files to pack')

        output_path = Path(output_path)

        image = Md1Image()
        image.file_mapping = self.file_mapping
        base_address = 0

        for file_path in self.files:
            file_name = file_path.name

            if 'md1_file_map' in file_name:
                continue

            stripped_name = strip_number(file_name)

            mapped_name = stripped_name
            for key, value in self.file_mapping.items():
                if to_lowercase(key) == to_lowercase(stripped_name):
                    mapped_name = value
                    break

                if (
                    to_lowercase(key) == to_lowercase(stripped_name) + '.gz'
                    or to_lowercase(key) == to_lowercase(stripped_name) + '.xz'
                ):
                    mapped_name = value
                    break

            try:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
            except (OSError, IOError) as e:
                raise InvalidIOFile(f'Failed to read file: {e}', file_path)

            compress_to = None
            for key, value in self.file_mapping.items():
                if value == mapped_name:
                    if key.lower().endswith('.gz'):
                        compress_to = CompressionFormat.GZIP
                    elif key.lower().endswith('.xz'):
                        compress_to = CompressionFormat.XZ
                    break

            if compress_to == CompressionFormat.GZIP:
                try:
                    file_data = compress_gz(file_data)
                    logger.info(f'Compressed {file_name} using gzip')
                except Exception as e:
                    logger.warning(
                        f'Failed to compress {file_name} with gzip: {e}'
                    )

            elif compress_to == CompressionFormat.XZ:
                try:
                    file_data = compress_xz(file_data)
                    logger.info(f'Compressed {file_name} using xz')
                except Exception as e:
                    logger.warning(
                        f'Failed to compress {file_name} with xz: {e}'
                    )

            if mapped_name in self.meta_info:
                meta = self.meta_info[mapped_name]

                header = Md1Header.create(mapped_name, len(file_data))

                if 'base' in meta:
                    try:
                        header.base = int(meta['base'], 16)
                    except ValueError:
                        pass

                if 'mode' in meta:
                    try:
                        header.mode = int(meta['mode'], 16)
                    except ValueError:
                        pass

                if 'hdr_version' in meta:
                    try:
                        header.hdr_version = int(meta['hdr_version'], 16)
                    except ValueError:
                        pass

                if 'img_type' in meta:
                    try:
                        header.img_type = int(meta['img_type'], 16)
                    except ValueError:
                        pass

                if 'img_list_end' in meta:
                    try:
                        header.img_list_end = int(meta['img_list_end'], 16)
                    except ValueError:
                        pass

                if 'align_size' in meta:
                    try:
                        header.align_size = int(meta['align_size'], 16)
                    except ValueError:
                        pass

                if 'dsize_extend' in meta:
                    try:
                        header.dsize_extend = int(meta['dsize_extend'], 16)
                    except ValueError:
                        pass

                if 'maddr_extend' in meta:
                    try:
                        header.maddr_extend = int(meta['maddr_extend'], 16)
                    except ValueError:
                        pass
            else:
                header = Md1Header.create(
                    mapped_name, len(file_data), base_address
                )

            md1_file = Md1File(
                name=mapped_name, header=header, data=file_data, offset=0
            )
            image.files.append(md1_file)

            file_size = header.data_offset + len(file_data)
            if file_size % 16 != 0:
                file_size += 16 - (file_size % 16)
            base_address += file_size

            logger.info(
                f'Packed {file_name} as {mapped_name} (size: {len(file_data)} bytes)'
            )

        if self.file_mapping:
            map_content = ''
            for key, value in self.file_mapping.items():
                map_content += f'{key}={value}\n'

            map_data = bytearray(504)

            for i, b in enumerate(bytes('md1_file_map', 'ascii')):
                if i < len(map_data):
                    map_data[i] = b

            map_data.extend(map_content.encode('utf-8'))
            map_header = Md1Header.create(
                'md1_file_map', len(map_data), base_address
            )
            map_file = Md1File(
                name='md1_file_map',
                header=map_header,
                data=bytes(map_data),
                offset=0,
            )
            image.files.append(map_file)

            logger.info('Added file mapping to image')

        try:
            image.save(output_path)
            logger.info(f'Successfully saved MD1 image to {output_path}')
            return output_path
        except (OSError, IOError) as e:
            raise InvalidIOFile(
                f'Failed to write output file: {e}', output_path
            )

    def find_compression_type(
        self, file_name: str
    ) -> Optional[CompressionFormat]:
        """
        Determine the compression format required for a file.

        Args:
            file_name: Name of the file to check

        Returns:
            CompressionFormat or None if no compression needed
        """
        stripped_name = strip_number(file_name)
        stripped_lower = to_lowercase(stripped_name)

        for key, value in self.file_mapping.items():
            key_lower = to_lowercase(key)

            if stripped_lower == key_lower:
                return None

            if key_lower.endswith('.gz') and stripped_lower == key_lower[:-3]:
                return CompressionFormat.GZIP

            if key_lower.endswith('.xz') and stripped_lower == key_lower[:-3]:
                return CompressionFormat.XZ

        return (
            self.config.compression_format
            if self.config.compression_format != CompressionFormat.NONE
            else None
        )
