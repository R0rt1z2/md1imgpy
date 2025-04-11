"""
SPDX-FileCopyrightText: 2025 Roger Ortiz <me@r0rt1z2.com>
SPDX-License-Identifier: GPL-3.0-or-later
"""

from __future__ import annotations

import gzip
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

try:
    import lzma

    LZMA_AVAILABLE = True
except ImportError:
    LZMA_AVAILABLE = False

from md1imgpy.exceptions import InvalidIOFile, Md1ImgError

logger = logging.getLogger(__name__)


def create_backup(image_path: Path, backup_dir: Optional[Path] = None) -> Path:
    """
    Create a backup of the original image.

    Args:
        image_path: Path to the image to back up
        backup_dir: Optional directory to store backup in

    Returns:
        Path to the backup file

    Raises:
        InvalidIOFile: If backup creation fails
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'{image_path.stem}_backup_{timestamp}{image_path.suffix}'

    if backup_dir:
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / backup_name
    else:
        backup_path = image_path.parent / backup_name

    try:
        shutil.copy2(image_path, backup_path)
        return backup_path
    except OSError as e:
        raise InvalidIOFile(str(e), backup_path)


def extract_number(filename: str) -> int:
    """
    Extract the numerical prefix from a filename.

    Args:
        filename: Filename to extract number from

    Returns:
        Extracted number, or 0 if no number found
    """
    match = re.match(r'^\d+', filename)
    if match:
        return int(match.group(0))
    return 0


def strip_number(filename: str) -> str:
    """
    Strip the numerical prefix from a filename.

    Args:
        filename: Filename to strip prefix from

    Returns:
        Filename without numerical prefix
    """
    match = re.match(r'^(\d+)_(.+)$', filename)
    if match:
        return match.group(2)
    return filename


def to_lowercase(text: str) -> str:
    """
    Convert text to lowercase.

    Args:
        text: Text to convert

    Returns:
        Lowercase text
    """
    return text.lower()


def ends_with(text: str, suffix: str) -> bool:
    """
    Check if text ends with a specific suffix.

    Args:
        text: Text to check
        suffix: Suffix to check for

    Returns:
        True if text ends with suffix, False otherwise
    """
    return text.endswith(suffix)


def compress_gz(data: bytes) -> bytes:
    """
    Compress data using gzip.

    Args:
        data: Data to compress

    Returns:
        Compressed data
    """
    return gzip.compress(data, compresslevel=9)


def decompress_gz(data: bytes) -> bytes:
    """
    Decompress gzipped data.

    Args:
        data: Compressed data

    Returns:
        Decompressed data

    Raises:
        Md1ImgError: If decompression fails
    """
    try:
        return gzip.decompress(data)
    except gzip.BadGzipFile as e:
        raise Md1ImgError(f'Error decompressing gzip data: {e}')


def compress_xz(data: bytes) -> bytes:
    """
    Compress data using xz/lzma.

    Args:
        data: Data to compress

    Returns:
        Compressed data

    Raises:
        Md1ImgError: If LZMA compression is not available
    """
    if not LZMA_AVAILABLE:
        raise Md1ImgError(
            'LZMA compression is not available. Install the lzma module.'
        )

    return lzma.compress(data, preset=9)


def decompress_xz(data: bytes) -> bytes:
    """
    Decompress xz/lzma data.

    Args:
        data: Compressed data

    Returns:
        Decompressed data

    Raises:
        Md1ImgError: If LZMA decompression is not available or fails
    """
    if not LZMA_AVAILABLE:
        raise Md1ImgError(
            'LZMA decompression is not available. Install the lzma module.'
        )

    try:
        return lzma.decompress(data)
    except lzma.LZMAError as e:
        raise Md1ImgError(f'Error decompressing LZMA data: {e}')


def parse_meta_info(meta_info_content: str) -> Dict[str, Dict[str, str]]:
    """
    Parse meta_info file content.

    Args:
        meta_info_content: Content of meta_info file

    Returns:
        Dictionary of file metadata
    """
    result = {}
    current_name = None
    current_meta = {}

    for line in meta_info_content.splitlines():
        line = line.strip()
        if not line:
            if current_name:
                result[current_name] = current_meta
                current_name = None
                current_meta = {}
            continue

        parts = line.split('=', 1)
        if len(parts) != 2:
            continue

        key, value = parts
        if key == 'name':
            if current_name:
                result[current_name] = current_meta
                current_meta = {}
            current_name = value
        else:
            current_meta[key] = value

    if current_name:
        result[current_name] = current_meta

    return result


def read_file_mapping(mapping_content: str) -> Dict[str, str]:
    """
    Parse file mapping content.

    Args:
        mapping_content: Content of md1_file_map

    Returns:
        Dictionary mapping filenames to their actual paths
    """
    mapping = {}
    for line in mapping_content.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = line.split('=', 1)
        if len(parts) != 2:
            continue

        value, key = parts
        mapping[key] = value

    return mapping
