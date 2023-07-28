"""
	This package provides tools for parsing serialised data to recover their original underlying types.

	The `TypeParser` class provides configurable type inference and parsing. This can be initialised with different settings to, for example:
	- treat `inf` as either a float or a normal string
	- give exact Decimal values instead of floats
	- detect inline lists
"""


__version__ = "0.3.2"

from ._common import AnyScalar, AnyScalarType, AnyValue, AnyValueType, GenericValue, Nullable
from ._parser import TypeParser
from ._reduce_types import reduce_types

__all__ = ('TypeParser', 'reduce_types', 'Nullable')
