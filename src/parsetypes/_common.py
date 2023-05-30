from __future__ import annotations

from decimal import Decimal
from typing import Generic, Type, TypeVar, Union

from ._compat import TypeAlias


AnyScalar = Union[str, int, float, Decimal, bool, None]
AnyScalarType = Type[AnyScalar]


GenericValue: TypeAlias = str
"""Fallback type when a more specific type cannot be identified"""


S = TypeVar('S', bound=AnyScalar)
"""Generic TypeVar for the non-container types recognised by `parsetypes`"""


class Nullable(Generic[S]):
	"""
		Dummy container type that represents a scalar (`S`) that could also be None

		The type annotation `Nullable[S]` is treated as equivalent to `Union[S, types.NoneType]`, which will accept either a value of type `S` or the value `None`.

		This class should not be instantiated.
	"""
	pass


AnyContainerBase: TypeAlias = Union[Nullable, list]
AnyContainerBaseType: TypeAlias = Type[AnyContainerBase]

AnyBase: TypeAlias = Union[AnyScalar, AnyContainerBase]
AnyBaseType: TypeAlias = Type[AnyBase]


AnyValue: TypeAlias = Union[str, int, float, Decimal, bool, None, list]
"""Union of all types recognised by `parsetypes`"""

AnyValueType: TypeAlias = Type[Union[str, int, float, Decimal, bool, None, Nullable, list]]
"""Type alias for all types recognised by `parsetypes`"""
