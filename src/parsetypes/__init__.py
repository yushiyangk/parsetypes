"""
	This package provides tools for parsing serialised data to recover their original underlying types.

    The `TypeParser` class provides configurable type inference and parsing. The `reduce_types()` function can be used to obtain consistent types for tabular data.
"""


__version__ = "0.1dev"

from ._common import GenericValue, Nullable, Scalar, Value, ValueType
from ._parser import TypeParser
from ._reduce_types import reduce_types

__all__ = ('TypeParser', 'reduce_types')
