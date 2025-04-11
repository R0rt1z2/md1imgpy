# md1imgpy

![License](https://img.shields.io/github/license/R0rt1z2/md1imgpy)
![GitHub Issues](https://img.shields.io/github/issues-raw/R0rt1z2/md1imgpy?color=red)
![CI](https://github.com/R0rt1z2/md1imgpy/actions/workflows/md1imgpy.yml/badge.svg)

`md1imgpy` is a Python tool for packing and unpacking MediaTek (modem) MD1 image files. It's a reimplementation of the original [md1img_repacker](https://github.com/blackeangel/md1img_repacker) tool by blackeangel.

## Installation

```bash
sudo apt install python3-pip # If you don't have pip installed.
pip3 install --upgrade pip   # If pip hasn't been updated yet.
pip3 install --upgrade git+https://github.com/R0rt1z2/md1imgpy
```
> <small>[!NOTE]
> _Windows users should omit the first two command(s) and install Python manually from [here](https://www.python.org/downloads/)._</small>

## Command-line Usage

```bash
python -m md1imgpy [command] [options]
```

### Commands

#### Unpack an MD1 image:
```bash
python -m md1imgpy unpack image.img -o output_dir
```

#### Pack a directory into an MD1 image:
```bash
python -m md1imgpy pack input_dir -o output.img
```

#### List files in an MD1 image:
```bash
python -m md1imgpy list image.img
```

### Command-line Options

#### Main Options:
```
-o, --output PATH           Output directory/file (default: based on input name)
-c, --config FILE           Path to configuration file (JSON)
```

#### Common Options:
```
--dry-run                   Perform a dry run without writing changes
--backup                    Create a backup before modifying files
--backup-dir DIR            Directory to store backups
--log-level LEVEL           Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
--log-file FILE             Log to specified file in addition to console
-v, --verbose               Print detailed information
```

#### Pack-Specific Options:
```
--compression FORMAT        Default compression format (none, gzip, xz) 
```

#### General Options:
```
--export-config FILE        Export default configuration to FILE and exit
--version                   Show version information and exit
-h, --help                  Show help message and exit
```

## Using as a Library

You can integrate md1imgpy into your own Python projects:

```python
from md1imgpy import Md1Image, Md1Unpacker, Md1Packer, Md1ImgConfig

# Unpack an image
image = Md1Image("md1img.img")
unpacker = Md1Unpacker(image)
unpacker.unpack("output_dir")

# Pack a directory
config = Md1ImgConfig()
config.compression_format = "GZIP" # (optional)
packer = Md1Packer(config)
packer.add_directory("input_dir")
packer.pack("output.img")

# List files in an image
image = Md1Image("md1img.img")
for file in image.get_file_names():
    print(file)
```

## File Format

MD1 images contain multiple files, each with its own header:

- **Header**: Fixed size structure with magic numbers, name, size, and other metadata
- **Data**: The actual file content
- **Padding**: Alignment to (usually) 16-byte boundaries
- **File Mapping**: Special file with mappings between internal and external filenames

The tool automatically handles compression formats:
- GZIP (.gz): Common compression format
- XZ (.xz): More efficient compression but requires the optional lzma module

## Configuration

Customize behavior with a JSON configuration file:

```json
{
  "log_level": "INFO",
  "backup": true,
  "backup_dir": "./backups",
  "compression_format": "GZIP",
  "dry_run": false,
  "verbose": false
}
```

## Acknowledgments

This project is a Python reimplementation of the original [md1img_repacker](https://github.com/blackeangel/md1img_repacker) C++ tool by blackeangel.

## License

This project is licensed under the GNU General Public License v3 (GPL-3.0) - see the [LICENSE](LICENSE) file for details.
