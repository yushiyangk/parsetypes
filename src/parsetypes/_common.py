from __future__ import annotations

from decimal import Decimal
from types import NoneType
from typing import Optional, Generic, Type, TypeVar, Union


Scalar = TypeVar('Scalar', str, int, float, Decimal, bool, None)


class Nullable(Generic[Scalar]):
	"""
		Dummy container type that represents a scalar value that can also be None.

		The type annotation `Nullable[S]` is treated as equivalent to `Union[S, types.NoneType]`, which matches either a value of type `T` or the value `None`.
	"""
	...

Datum = TypeVar('Datum',
	str, int, float, Decimal, bool, None,
	Nullable[str], Nullable[int], Nullable[float], Nullable[Decimal], Nullable[bool], Nullable[None],
	list[str], list[int], list[float], list[Decimal], list[bool], list[None],
	list[Nullable[str]], list[Nullable[int]], list[Nullable[float]], list[Nullable[Decimal]], list[Nullable[bool]], list[Nullable[None]],
)
DatumType = Type[Datum]
GenericDatum = str

type_names: dict[str, DatumType] = {
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
