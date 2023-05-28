from __future__ import annotations

from decimal import Decimal
from typing import Generic, Type, TypeAlias, TypeVar, Union


AnyScalar = Union[str, int, float, Decimal, bool, None]
AnyScalarType = Type[AnyScalar]


GenericValue: TypeAlias = str
"""Fallback type when a more specific type cannot be identified"""


S = TypeVar('S', bound=AnyScalar)
"""Generic TypeVar of the non-container types recognised by `parsetypes`"""


class Nullable(Generic[S]):
	"""
		Dummy container type that represents a scalar (`S`) that could also be None

		The type annotation `Nullable[S]` is treated as equivalent to `Union[S, types.NoneType]`, which will accept either a value of type `S` or the value `None`.
	"""
	pass


AnyContainerBase: TypeAlias = Union[Nullable, list]
AnyContainerBaseType: TypeAlias = Type[AnyContainerBase]

AnyBase: TypeAlias = Union[AnyScalar, AnyContainerBase]
AnyBaseType: TypeAlias = Type[AnyBase]

AnyNullable: TypeAlias = Union[Nullable[str], Nullable[int], Nullable[float], Nullable[Decimal], Nullable[bool], Nullable[None]]
AnyNullableType: TypeAlias = Type[AnyNullable]

AnyContained: TypeAlias = Union[AnyScalar, AnyNullable]
AnyContainedType: TypeAlias = Type[AnyContained]



AnyValue = Union[
	str, int, float, Decimal, bool, None,
	Nullable[str], Nullable[int], Nullable[float], Nullable[Decimal], Nullable[bool], Nullable[None],
	list[str], list[int], list[float], list[Decimal], list[bool], list[None],
	list[Nullable[str]], list[Nullable[int]], list[Nullable[float]], list[Nullable[Decimal]], list[Nullable[bool]], list[Nullable[None]],
]
"""Union of all types recognised by `parsetypes`"""

AnyValueType: TypeAlias = Type[AnyValue]
"""Type alias for all types recognised by `parsetypes`"""
