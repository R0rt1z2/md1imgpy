"""
SPDX-FileCopyrightText: 2025 Roger Ortiz <me@r0rt1z2.com>
SPDX-License-Identifier: GPL-3.0-or-later
"""

from pathlib import Path
from typing import Final

from md1imgpy.config import Md1ImgConfig
from md1imgpy.exceptions import (
    ConfigurationError,
    HeaderError,
    InvalidIOFile,
    MapFileNotFoundError,
    Md1ImgError,
)
from md1imgpy.image import Md1Image
from md1imgpy.packer import Md1Packer
from md1imgpy.unpacker import Md1Unpacker

__version__: Final[str] = '0.1.0'
__author__: Final[str] = 'Roger Ortiz <me@r0rt1z2.com>'
__description__: Final[str] = 'MediaTek MD1 image packer/unpacker'

module_path: Final[Path] = Path(__file__).parent
current_path: Final[Path] = Path.cwd()

__all__ = [
    # Classes
    'Md1Image',
    'Md1Unpacker',
    'Md1Packer',
    'Md1ImgConfig',
    # Exceptions
    'Md1ImgError',
    'InvalidIOFile',
    'MapFileNotFoundError',
    'ConfigurationError',
    'HeaderError',
    # Constants
    'module_path',
    'current_path',
    '__version__',
    '__author__',
    '__description__',
]
