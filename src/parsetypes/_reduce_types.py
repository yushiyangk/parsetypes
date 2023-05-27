import typing
from decimal import Decimal
from types import NoneType
from typing import Iterable, cast

from ._common import GenericValue, Nullable, ValueType


_TerminalValue = list

_type_hierarchy: dict[ValueType, ValueType | None] = {
	bool: int,
	int: Decimal,
	Decimal: float,
	float: str,
	str: Nullable,
	Nullable: list,
	list: None,
}
_containers: set[ValueType] = {Nullable, list}


def _is_valid_type(t: ValueType) -> bool:
	if t == NoneType:
		return True
	base = typing.get_origin(t)
	if base is None:
		return (t in _type_hierarchy)
	else:
		if base not in _type_hierarchy:
			return False
		if base not in _containers:
			return False
		for arg in typing.get_args(t):
			if not _is_valid_type(arg):
				return False
		return True


def _decompose_type(t: ValueType) -> tuple[ValueType, tuple[ValueType, ...] | None]:
	base = typing.get_origin(t)
	if base is None:
		return t, None
	else:
		return cast(ValueType, base), tuple(cast(ValueType, arg) for arg in typing.get_args(t))


def _broaden_type(t: ValueType, cue: ValueType | None=None) -> ValueType | None:
	base, type_args = _decompose_type(t)
	broadened = _type_hierarchy[base]
	if broadened is None:
		return None
	if base in _containers:
		if broadened in _containers:
			if type_args is not None and len(type_args) == 1:
				return broadened[type_args[0]]
			else:
				return broadened  # Must be able to broaden generic Nullable to list
		else:
			return broadened
	else:
		# base is Scalar
		if broadened in _containers:
			if cue is not None:
				cue_base, cue_args = _decompose_type(cue)
				print(cue)
				if cue_base not in _containers:
					return broadened[cue_base]
				else:
					assert False  # cue should have come before base, so should also be Scalar
			else:
				assert False  # Cue should always be given
		else:
			return broadened


def _merge_types(t1: ValueType, t2: ValueType) -> ValueType:
	if t1 == t2:
		return t1
	if (not _is_valid_type(t1)) or (not _is_valid_type(t2)):
		return GenericValue

	c: ValueType | None = t1
	visited: dict[ValueType, tuple[ValueType, ...] | None] = {}
	if t1 == NoneType:
		visited[NoneType] = None
		visited[Nullable] = None
	else:
		while c is not None:
			base, type_args = _decompose_type(c)
			if base not in visited:
				visited[base] = type_args
			if base == _TerminalValue:
				break
			c = _broaden_type(c, t1)

	if t2 == NoneType:
		if NoneType in visited:
			return NoneType
		else: c = Nullable
	else:
		c = t2
	while c is not None:
		base, type_args = _decompose_type(c)
		if base not in visited:
			c = _broaden_type(c, t2)
		else:
			visited_args = visited[base]
			if type_args is not None and len(type_args) == 1:
				if visited_args is not None and len(visited_args) == 1:
					merged_arg = _merge_types(type_args[0], visited_args[0])
					return base[merged_arg]
				else:
					return base[type_args[0]]
			else:
				if visited_args is not None and len(visited_args) == 1:
					return base[visited_args[0]]
				else:
					return base

	return GenericValue


def reduce_types(types: Iterable[ValueType]) -> ValueType:
	"""
		Reduce multiple types into a single common type.

		If the input types are not all the same, the resulting type will be narrowest possible type that will encompass all of the input types.

		This operation is useful in cases such as parsing a CSV file where each column should have a consistent type, but where the individual values in a column could be interpreted variously as ints or floats (or other types).

		Parameters
		----------
		`types`
		: types to be reduced

		Returns
		-------
		common reduced type

		Examples
		--------
		```python
		reduce_types([int, float])        # float
		reduce_types([bool, int])         # int
		reduce_types([int, float, str])   # str
		```
	"""
	reduced_type: ValueType | None = None
	for t in types:
		if reduced_type is None:
			reduced_type = t
		elif t != reduced_type:
			reduced_type = _merge_types(reduced_type, t)
		if reduced_type == _TerminalValue:
			return _TerminalValue

	if reduced_type is None:
		return GenericValue
	else:
		return reduced_type
