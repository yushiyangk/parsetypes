from __future__ import annotations

from decimal import Decimal
from types import NoneType
from typing import Generic, Type, TypeAlias, TypeVar


Scalar = TypeVar('Scalar', str, int, float, Decimal, bool, None)
"""Generic TypeVar of the non-container types recognised by `parsetypes`"""

class Nullable(Generic[Scalar]):
	"""
		Dummy container type that represents a Scalar that could also be None

		The type annotation `Nullable[Scalar]` is treated as equivalent to `Union[Scalar, types.NoneType]`, which will accept either a value of type `Scalar` or the value `None`.
	"""
	pass

Value = TypeVar('Value',
	str, int, float, Decimal, bool, None,
	Nullable[str], Nullable[int], Nullable[float], Nullable[Decimal], Nullable[bool], Nullable[None],
	list[str], list[int], list[float], list[Decimal], list[bool], list[None],
	list[Nullable[str]], list[Nullable[int]], list[Nullable[float]], list[Nullable[Decimal]], list[Nullable[bool]], list[Nullable[None]],
)
"""Generic TypeVar of all types recognised by `parsetypes`"""

ValueType: TypeAlias = Type[Value]
"""This type annotation will accept any of the type objects (or class objects) accepted by `Value`"""

GenericValue: TypeAlias = str
"""Fallback type when a more specific type cannot be identified"""

type_names: dict[str, ValueType] = {
	'str': str,
	'int': int,
	'float': float,
	'decimal': Decimal,
	'bool': bool,

	'none': NoneType,
	'NoneTypetype': NoneType,
	'null': NoneType,
	'nil': NoneType,
	'void': NoneType,

	'list': list,
	'sequence': list,
	'array': list,

	#'dict': dict,
	#'mapping': dict,
	#'dictionary': dict,
	#'map': dict,
	#'hashmap': dict,
	#'table': dict,
	#'hashtable': dict,

	'string': str,
	'integer': int,
	'boolean': bool,
}
