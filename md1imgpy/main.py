"""
SPDX-FileCopyrightText: 2025 Roger Ortiz <me@r0rt1z2.com>
SPDX-License-Identifier: GPL-3.0-or-later
"""

from __future__ import annotations

import logging
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path
from typing import List, Optional

from md1imgpy import (
    __author__,
    __description__,
    __version__,
)
from md1imgpy.config import CompressionFormat, LogLevel, Md1ImgConfig
from md1imgpy.exceptions import (
    ConfigurationError,
    Md1ImgError,
)
from md1imgpy.image import Md1Image
from md1imgpy.packer import Md1Packer
from md1imgpy.unpacker import Md1Unpacker
from md1imgpy.utils import create_backup


def setup_logging(log_level: LogLevel, log_file: Optional[Path] = None) -> None:
    """
    Set up logging configuration.

    Args:
        log_level: Logging level to use
        log_file: Optional file to log to in addition to console
    """
    handlers: List[logging.Handler] = [logging.StreamHandler()]

    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            handlers.append(file_handler)
        except OSError as e:
            print(f'Warning: Could not create log file ({e})', file=sys.stderr)

    logging.basicConfig(
        level=log_level.to_logging_level(),
        format='[%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers,
    )


def list_files(image_path: Path) -> int:
    """
    List all files in an MD1 image.

    Args:
        image_path: Path to the image file

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        image = Md1Image(image_path)
        unpacker = Md1Unpacker(image)
        files = unpacker.list_files()

        if not files:
            print('No files found in image.')
            return 0

        print(f'\nFiles in MD1 image: {image_path}')
        print('-' * 60)
        print(
            f'{"#":<4} {"Name":<20} {"Mapped Name":<20} {"Size":<10} {"Base":<10} {"Compression":<10}'
        )
        print('-' * 60)

        for info in files:
            print(
                f'{info["index"]:<4} {info["name"]:<20} {info["mapped_name"]:<20} {info["size"]:<10} {info["base"]:<10} {info["compression"]:<10}'
            )

        print('-' * 60)
        print(f'Total: {len(files)} files')

        return 0
    except Md1ImgError as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1


def export_config(output_path: Path) -> int:
    """
    Export default configuration to a file.

    Args:
        output_path: Path to save configuration to

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    config = Md1ImgConfig()

    try:
        config.save(output_path)
        print(f'Configuration exported to {output_path}')
        return 0
    except ConfigurationError as e:
        print(f'Error exporting configuration: {e}', file=sys.stderr)
        return 1


def main() -> int:
    """
    Main entry point for the MD1 image tool.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = ArgumentParser(
        prog='python3 -m md1imgpy',
        description=f'{__description__} v{__version__}\nBy {__author__}',
        formatter_class=RawDescriptionHelpFormatter,
        epilog='Examples:\n'
        '  %(prog)s unpack image.img                   # Unpack with default settings\n'
        '  %(prog)s unpack image.img -o output_dir     # Specify output directory\n'
        '  %(prog)s pack input_dir -o output.img       # Pack directory into image\n'
        '  %(prog)s list image.img                     # List files in image\n'
        '  %(prog)s --export-config config.json        # Export default config',
    )

    subparsers = parser.add_subparsers(
        dest='command', help='Command to execute'
    )

    unpack_parser = subparsers.add_parser('unpack', help='Unpack an MD1 image')
    unpack_parser.add_argument(
        'image', type=Path, help='Path to the image file'
    )
    unpack_parser.add_argument(
        '-o',
        '--output',
        type=Path,
        help='Output directory (default: image name)',
    )

    pack_parser = subparsers.add_parser(
        'pack', help='Pack files into an MD1 image'
    )
    pack_parser.add_argument(
        'directory', type=Path, help='Directory with files to pack'
    )
    pack_parser.add_argument(
        '-o',
        '--output',
        type=Path,
        help='Output image file (default: directory-new.img)',
    )
    pack_parser.add_argument(
        '--compression',
        choices=['none', 'gzip', 'xz'],
        default='none',
        help='Default compression format for files without mapping',
    )

    list_parser = subparsers.add_parser(
        'list', help='List files in an MD1 image'
    )
    list_parser.add_argument('image', type=Path, help='Path to the image file')

    for subparser in [unpack_parser, pack_parser, list_parser]:
        subparser.add_argument(
            '-c',
            '--config',
            type=Path,
            help='Path to configuration file (JSON)',
        )
        subparser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without writing changes',
        )
        subparser.add_argument(
            '--backup',
            action='store_true',
            help='Create a backup before modifying files',
        )
        subparser.add_argument(
            '--backup-dir', type=Path, help='Directory to store backups'
        )
        subparser.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='INFO',
            help='Set logging level',
        )
        subparser.add_argument(
            '--log-file',
            type=Path,
            help='Log to specified file in addition to console',
        )
        subparser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            help='Print detailed information',
        )

    parser.add_argument(
        '--export-config',
        type=Path,
        metavar='FILE',
        help='Export default configuration to FILE and exit',
    )

    parser.add_argument(
        '--version', action='version', version=f'%(prog)s {__version__}'
    )

    args = parser.parse_args()

    if args.export_config:
        return export_config(args.export_config)

    if not args.command:
        parser.print_help()
        return 0

    config = Md1ImgConfig()
    if hasattr(args, 'config') and args.config:
        try:
            config = Md1ImgConfig.from_file(args.config)
        except ConfigurationError as e:
            print(f'Configuration error: {e}', file=sys.stderr)
            return 1

    if hasattr(args, 'log_level'):
        config.log_level = LogLevel.from_string(args.log_level)
    if hasattr(args, 'backup'):
        config.backup = args.backup
    if hasattr(args, 'backup_dir'):
        config.backup_dir = args.backup_dir
    if hasattr(args, 'dry_run'):
        config.dry_run = args.dry_run
    if hasattr(args, 'verbose'):
        config.verbose = args.verbose
    if hasattr(args, 'compression'):
        config.compression_format = CompressionFormat.from_string(
            args.compression
        )

    setup_logging(
        config.log_level, args.log_file if hasattr(args, 'log_file') else None
    )
    logger = logging.getLogger(__name__)

    logger.info(f'MD1 Image Tool - version {__version__}')

    try:
        if args.command == 'unpack':
            if not args.output:
                output_dir = args.image.parent / args.image.stem
            else:
                output_dir = args.output

            if config.backup and not config.dry_run:
                backup_path = create_backup(args.image, config.backup_dir)
                logger.info(f'Created backup at {backup_path}')

            unpacker = Md1Unpacker(args.image, config)

            if config.dry_run:
                logger.info(
                    f'Dry run: would unpack {args.image} to {output_dir}'
                )
                return 0

            extracted_files = unpacker.unpack(output_dir)
            logger.info(
                f'Successfully unpacked {len(extracted_files)} files to {output_dir}'
            )

        elif args.command == 'pack':
            if not args.output:
                output_file = (
                    args.directory.parent / f'{args.directory.stem}-new.img'
                )
            else:
                output_file = args.output

            packer = Md1Packer(config)
            packer.add_directory(args.directory)

            if config.dry_run:
                logger.info(
                    f'Dry run: would pack {args.directory} to {output_file}'
                )
                return 0

            result_path = packer.pack(output_file)
            logger.info(f'Successfully packed to {result_path}')

        elif args.command == 'list':
            return list_files(args.image)

        return 0

    except Md1ImgError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.exception(f'Unexpected error: {e}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
