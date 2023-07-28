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

Found a bug? Please [report an issue](https://github.com/yushiyangk/parsetypes/issues), or, better yet, [contribute a bugfix](https://github.com/yushiyangk/parsetypes/blob/main/CONTRIBUTING.md).
