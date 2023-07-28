# parsetypes

This Python package provides tools for parsing serialised data to recover their original underlying types.

[![](https://img.shields.io/badge/PyPI--inactive?style=social&logo=pypi)](https://pypi.org/project/parsetypes/) [![](https://img.shields.io/badge/GitHub--inactive?style=social&logo=github)](https://github.com/yushiyangk/parsetypes) [![](https://img.shields.io/badge/Documentation--inactive?style=social&logo=readthedocs)](https://parsetypes.gnayihs.uy/)

## Overview

The `TypeParser` class provides configurable type inference and parsing. This can be [initialised with different settings](https://parsetypes.gnayihs.uy/parsetypes.html#TypeParser.__init__) to, for example:
- allow `None` (null values) or not
- treat `inf` as either a float or a normal string
- give exact Decimal values instead of floats
- detect inline lists

## Install

```
pip install parsetypes
```

## Basic examples

Import parser:
```python
from parsetypes import TypeParser
```

Parse a single value:
```python
parser = TypeParser()
parser.parse("1.2")   # 1.2
parser.parse("true")  # True
parser.parse("")      # None
```

Parse a series so that it has a consistent type:
```python
parser = TypeParser()
parser.parse_series(["0", "1", "2"])         # [0, 1, 2]
parser.parse_series(["0", "1.2", ""])        # [0.0, 1.2, None]
parser.parse_series(["false", "true", ""])   # [False, True, None]
parser.parse_series(["false", "true", "2"])  # [0, 1, 2]
parser.parse_series(["1", "2.3", "abc"])     # ["1", "2.3", "abc"]
```

Parse a table so that each column is of a consistent type:
```python
parser = TypeParser()
table = parser.parse_table([
	["0", "3",   "false", "false", "7"],
	["1", "4.5", "true",  "true",  "8.9"],
	["2", "",    "",      "6",     "abc"],
]):
assert table == [
	[0, 3.0,  False, 0, "7"],
	[1, 4.5,  True,  1, "8.9"],
	[2, None, None,  6, "abc"],
]
```

The main contribution of this module lies in the [`infer_series()`](https://parsetypes.gnayihs.uy/parsetypes.html#TypeParser.infer_series) and [`infer_table()`](https://parsetypes.gnayihs.uy/parsetypes.html#TypeParser.infer_table) functions, which are also called by `parse_series()` and `parse_table()`.

## Issues

Found a bug? Please [file an issue](https://github.com/yushiyangk/parsetypes/issues), or, better yet, [submit a pull request](https://github.com/yushiyangk/parsetypes/pulls).

## Development

Clone the repository with `git clone https://github.com/yushiyangk/parsetypes.git`.

The source for the package is `src/`, with tests in `tests/`.

### Virtual environment

Create the venv using `python -m venv .`.

To activate the venv, on Linux run `source Scripts/activate`, and on Windows run `Scripts/Activate.ps1` or `Scripts/activate.bat`.

Later, to deactivate the venv, run `deactivate`.

### Dependencies

Run `pip install -r requirements.dev.txt`.

### Install

To install the package locally (in the venv) for development, run `pip install -e .`.

### Tasks

For unit tests, run `pytest`.

To run unit tests across all supported Python versions, run `tox p -m testall`. This is slower than just `pytest`. Note that only Python versions that are installed locally will be run.

To run the full set of tasks before package publication, run `tox p -m prepare`. Alternatively, see below for manually running individual steps in this process.

#### Unit tests

Run `pytest` or `coverage run -m pytest`.

For coverage report, first run `coverage run -m pytest`, then either `coverage report -m` to print to stdout or `coverage html` to generate an HTML report in `htmlcov/`. Alternatively, run `tox r -m test` to do both steps automatically (slower).

#### Documentation

Run `tox r -m docs`.

The documentation is generated in `docs/html/`, using template files in `docs/template/`.

#### Packaging

Before packaging, check the package metadata by running `pyroma .` or `tox r -m metadata`.

To generate sdist and wheel packages, delete `dist/` and `parsetypes.egg-info/` if they exist, then run `python -m build`. Run `twine check dist/*` to check that the packages were generated properly. Alternatively, run `tox r -m package` to do these steps automatically.

### Config files

- `MANIFEST.in` Additional files to include in published sdist package
- `pyproject.toml` Package metadata, as well as configs for test and build tools
- `requirements.dev.txt` Package dependencies for development, in pip format
- `requirements.publish.txt` Package dependencies for publishing, in pip format
- `tox.ini` Config file for tox
