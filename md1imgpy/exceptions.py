"""
SPDX-FileCopyrightText: 2025 Roger Ortiz <me@r0rt1z2.com>
SPDX-License-Identifier: GPL-3.0-or-later
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union


class Md1ImgError(Exception):
    """Base exception for MD1 image-related errors."""

    def __init__(self, message: str):
        """
        Initialize the MD1 image error.

        Args:
            message: Descriptive error message
        """
        super().__init__(message)
        self.message = message


class InvalidIOFile(Md1ImgError):
    """
    Raised when a file cannot be read or written.

    Attributes:
        file: Path to the file that caused the error
        reason: Specific reason for I/O failure
    """

    def __init__(self, reason: str, file: Union[str, Path]):
        """
        Initialize the invalid I/O file error.

        Args:
            reason: Reason for I/O failure
            file: Path to the file that caused the error
        """
        super().__init__(f'Unable to access {file}: {reason}')
        self.file = file
        self.reason = reason


class MapFileNotFoundError(Md1ImgError):
    """
    Raised when the md1_file_map is not found in the image.

    Attributes:
        image: Path to the image where the map file was not found
    """

    def __init__(self, image: Union[str, Path]):
        """
        Initialize the map file not found error.

        Args:
            image: Path to the image where the map file was not found
        """
        super().__init__(f'md1_file_map not found in {image}')
        self.image = image


class ConfigurationError(Md1ImgError):
    """
    Raised when there's an error in the configuration.

    Attributes:
        config_file: Optional path to the configuration file
        detail: Detailed description of the configuration error
    """

    def __init__(
        self, detail: str, config_file: Optional[Union[str, Path]] = None
    ):
        """
        Initialize the configuration error.

        Args:
            detail: Detailed description of the configuration error
            config_file: Optional path to the configuration file
        """
        message = f'Configuration error: {detail}'
        if config_file:
            message = f'{message} (in {config_file})'
        super().__init__(message)
        self.detail = detail
        self.config_file = config_file


class HeaderError(Md1ImgError):
    """
    Raised when a header cannot be parsed correctly.

    Attributes:
        detail: Detailed description of the header error
    """

    def __init__(self, detail: str):
        """
        Initialize the header error.

        Args:
            detail: Detailed description of the header error
        """
        super().__init__(f'Header error: {detail}')
        self.detail = detail
