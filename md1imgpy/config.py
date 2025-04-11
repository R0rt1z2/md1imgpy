"""
SPDX-FileCopyrightText: 2025 Roger Ortiz <me@r0rt1z2.com>
SPDX-License-Identifier: GPL-3.0-or-later
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, Optional, Union

from md1imgpy.exceptions import ConfigurationError


class LogLevel(Enum):
    """Log levels for the md1img tool."""

    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

    @classmethod
    def from_string(cls, value: str) -> LogLevel:
        """
        Convert string representation to LogLevel enum.

        Args:
            value: String representation of log level

        Returns:
            Corresponding LogLevel enum value

        Raises:
            ValueError: If string doesn't match any log level
        """
        value = value.upper()
        try:
            return cls[value]
        except KeyError:
            valid_levels = [level.name for level in cls]
            raise ValueError(
                f'Invalid log level: {value}. Valid levels: {", ".join(valid_levels)}'
            )

    def to_logging_level(self) -> int:
        """
        Convert to Python's logging module level.

        Returns:
            Corresponding logging module level as integer
        """
        return {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
        }[self]


class CompressionFormat(Enum):
    """Compression formats supported by md1img."""

    NONE = auto()
    GZIP = auto()
    XZ = auto()

    @classmethod
    def from_string(cls, value: str) -> CompressionFormat:
        """
        Convert string representation to CompressionFormat enum.

        Args:
            value: String representation of compression format

        Returns:
            Corresponding CompressionFormat enum value

        Raises:
            ValueError: If string doesn't match any format
        """
        value = value.upper()
        if value in ('GZ', 'GZIP'):
            return cls.GZIP
        elif value in ('XZ', 'LZMA'):
            return cls.XZ
        elif value in ('NONE', 'RAW'):
            return cls.NONE
        else:
            valid_formats = ['NONE', 'GZIP', 'XZ']
            raise ValueError(
                f'Invalid compression format: {value}. Valid formats: {", ".join(valid_formats)}'
            )


@dataclass
class Md1ImgConfig:
    """
    Configuration for the MD1 image tool.

    Attributes:
        log_level: Logging level for the tool
        backup: Whether to create backups before modifying
        backup_dir: Directory for storing backups
        compression_format: Default compression format for files
        dry_run: Whether to perform a dry run without writing changes
        verbose: Whether to print detailed information
    """

    log_level: LogLevel = LogLevel.INFO
    backup: bool = False
    backup_dir: Optional[Path] = None
    compression_format: CompressionFormat = CompressionFormat.NONE
    dry_run: bool = False
    verbose: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Md1ImgConfig:
        """
        Create configuration from dictionary.

        Args:
            data: Dictionary containing configuration values

        Returns:
            Md1ImgConfig instance

        Raises:
            ConfigurationError: If configuration is invalid
        """
        config = cls()

        try:
            if 'log_level' in data:
                config.log_level = LogLevel.from_string(data['log_level'])

            for bool_field in ['backup', 'dry_run', 'verbose']:
                if bool_field in data:
                    setattr(config, bool_field, bool(data[bool_field]))

            if 'backup_dir' in data:
                backup_dir = Path(data['backup_dir'])
                if not backup_dir.exists():
                    backup_dir.mkdir(parents=True, exist_ok=True)
                config.backup_dir = backup_dir

            if 'compression_format' in data:
                config.compression_format = CompressionFormat.from_string(
                    data['compression_format']
                )

        except (ValueError, TypeError, OSError) as e:
            raise ConfigurationError(str(e))

        return config

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> Md1ImgConfig:
        """
        Load configuration from a JSON file.

        Args:
            file_path: Path to the JSON configuration file

        Returns:
            Md1ImgConfig instance

        Raises:
            ConfigurationError: If file cannot be read or parsed
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except FileNotFoundError:
            raise ConfigurationError('Configuration file not found', file_path)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f'Invalid JSON: {e}', file_path)
        except Exception as e:
            raise ConfigurationError(str(e), file_path)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return {
            'log_level': self.log_level.name,
            'backup': self.backup,
            'backup_dir': str(self.backup_dir) if self.backup_dir else None,
            'compression_format': self.compression_format.name,
            'dry_run': self.dry_run,
            'verbose': self.verbose,
        }

    def save(self, file_path: Union[str, Path]) -> None:
        """
        Save configuration to a JSON file.

        Args:
            file_path: Path where configuration will be saved

        Raises:
            ConfigurationError: If file cannot be written
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=4)
        except (OSError, IOError) as e:
            raise ConfigurationError(
                f'Failed to save configuration: {e}', file_path
            )
