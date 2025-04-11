"""
SPDX-FileCopyrightText: 2025 Roger Ortiz <me@r0rt1z2.com>
SPDX-License-Identifier: GPL-3.0-or-later
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from md1imgpy.config import Md1ImgConfig
from md1imgpy.exceptions import InvalidIOFile
from md1imgpy.image import Md1Image
from md1imgpy.structures import is_gz_format, is_xz_format
from md1imgpy.utils import (
    decompress_gz,
    decompress_xz,
)

logger = logging.getLogger(__name__)


class Md1Unpacker:
    """
    Unpacks files from an MD1 image.

    Provides functionality to extract files from an MD1 image
    and write them to disk, handling decompression as needed.

    Attributes:
        image: The MD1 image to unpack
        config: Configuration for the unpacker
    """

    def __init__(
        self,
        image: Union[str, Path, Md1Image],
        config: Optional[Md1ImgConfig] = None,
    ):
        """
        Initialize the unpacker.

        Args:
            image: Path to image file or Md1Image instance
            config: Optional configuration settings
        """
        self.config = config or Md1ImgConfig()

        if isinstance(image, (str, Path)):
            self.image = Md1Image(image)
        else:
            self.image = image

        logger.info(
            f'Initialized unpacker for image with {len(self.image.files)} files'
        )

    def unpack(self, output_dir: Union[str, Path]) -> List[Path]:
        """
        Unpack all files from the image to the output directory.

        Args:
            output_dir: Directory where to extract files

        Returns:
            List of paths to extracted files

        Raises:
            InvalidIOFile: If files cannot be written
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        extracted_files = []
        file_counter = 1

        meta_info_path = output_dir / 'meta_info'
        try:
            with open(meta_info_path, 'w') as f:
                for md1_file in self.image.files:
                    if md1_file.name == 'md1_file_map':
                        continue

                    f.write(f'name={md1_file.name}\n')
                    header_dict = md1_file.header.to_dict()
                    for key, value in header_dict.items():
                        if key != 'name':
                            f.write(f'{key}={value}\n')
                    f.write('\n')

            extracted_files.append(meta_info_path)
            logger.info(f'Created meta_info file: {meta_info_path}')
        except (OSError, IOError) as e:
            raise InvalidIOFile(
                f'Failed to write meta_info: {e}', meta_info_path
            )

        for md1_file in self.image.files:
            mapped_name = None
            for actual_name, internal_name in self.image.file_mapping.items():
                if internal_name == md1_file.name:
                    mapped_name = actual_name
                    break

            if mapped_name:
                output_name = f'{file_counter}_{mapped_name}'
            else:
                output_name = f'{file_counter}_{md1_file.name}'

            output_path = output_dir / output_name

            try:
                data = md1_file.data
                need_decompress = False

                if is_gz_format(data):
                    need_decompress = True
                    decompressed_data = decompress_gz(data)

                    if not mapped_name and output_path.suffix.lower() == '.gz':
                        output_path = output_path.with_suffix('')

                elif is_xz_format(data):
                    need_decompress = True
                    decompressed_data = decompress_xz(data)
                    logger.info(f'Decompressed {output_name} (xz)')

                    if not mapped_name and output_path.suffix.lower() == '.xz':
                        output_path = output_path.with_suffix('')

                with open(output_path, 'wb') as f:
                    if need_decompress:
                        f.write(decompressed_data)
                        logging.info(
                            f'Decompressed {output_name} to {output_path}'
                        )
                    else:
                        f.write(data)
                        logging.info(f'{output_name} written to {output_path}')

                extracted_files.append(output_path)

            except Exception as e:
                logger.error(f'Failed to extract {output_name}: {e}')

            file_counter += 1

        if self.image.file_mapping:
            map_path = output_dir / 'md1_file_map'
            try:
                with open(map_path, 'w') as f:
                    for key, value in self.image.file_mapping.items():
                        f.write(f'{key}={value}\n')

                extracted_files.append(map_path)
                logger.info(f'Created file mapping: {map_path}')

            except (OSError, IOError) as e:
                raise InvalidIOFile(
                    f'Failed to write file mapping: {e}', map_path
                )

        return extracted_files

    def extract_file(
        self,
        file_name: str,
        output_path: Optional[Union[str, Path]] = None,
        decompress: bool = True,
    ) -> Optional[Path]:
        """
        Extract a single file from the image.

        Args:
            file_name: Name of the file to extract
            output_path: Optional path where to save the file
            decompress: Whether to decompress the file if needed

        Returns:
            Path to the extracted file or None if file not found

        Raises:
            InvalidIOFile: If file cannot be written
        """
        md1_file = self.image.get_file_by_name(file_name)
        if not md1_file:
            logger.warning(f'File not found: {file_name}')
            return None

        if not output_path:
            mapped_name = None
            for actual_name, internal_name in self.image.file_mapping.items():
                if internal_name == file_name:
                    mapped_name = actual_name
                    break

            output_path = mapped_name or file_name

        output_path = Path(output_path)

        try:
            data = md1_file.data
            need_decompress = False

            if decompress:
                if is_gz_format(data):
                    need_decompress = True
                    data = decompress_gz(data)
                    logger.info(f'Decompressed {file_name} (gzip)')

                elif is_xz_format(data):
                    need_decompress = True
                    data = decompress_xz(data)
                    logger.info(f'Decompressed {file_name} (xz)')

            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                f.write(data)

            if need_decompress:
                print(f'Decompressed {file_name} to {output_path}')
            else:
                print(f'{file_name} written to {output_path}')

            return output_path

        except Exception as e:
            raise InvalidIOFile(
                f'Failed to extract {file_name}: {e}', output_path
            )

    def list_files(self) -> List[Dict[str, Any]]:
        """
        List all files in the image with their details.

        Returns:
            List of dictionaries with file information
        """
        result = []

        for i, md1_file in enumerate(self.image.files, 1):
            mapped_name = None
            for actual_name, internal_name in self.image.file_mapping.items():
                if internal_name == md1_file.name:
                    mapped_name = actual_name
                    break

            compression = 'none'
            if is_gz_format(md1_file.data):
                compression = 'gzip'
            elif is_xz_format(md1_file.data):
                compression = 'xz'

            file_info = {
                'index': i,
                'name': md1_file.name,
                'mapped_name': mapped_name or 'Unknown',
                'size': md1_file.size,
                'base': f'0x{md1_file.header.base:08x}',
                'offset': f'0x{md1_file.offset:08x}',
                'compression': compression,
            }

            result.append(file_info)

        return result
