import typing
from decimal import Decimal
from typing import Iterable, Optional, cast

from ._common import AnyBaseType, AnyContainerBaseType, AnyScalarType, AnyValueType, GenericValue, Nullable

from ._compat import Final, NoneType, Union


_TerminalValue: 'Final[AnyBaseType]' = list

_scalar_hierarchy: 'Final[dict[AnyBaseType, Union[AnyBaseType, None]]]' = {
	bool: int,
	int: Decimal,
	Decimal: float,
	float: str,
	str: None,
}
_containers: 'Final[set[AnyBaseType]]' = {Nullable, list}
_type_hierarchy: 'Final[dict[AnyBaseType, Union[AnyBaseType, None]]]' = {
	bool: int,
	int: Decimal,
	Decimal: float,
	float: str,
	str: Nullable,
	Nullable: list,
	list: None,
}


def _is_valid_type(t: AnyValueType) -> bool:
	if t == NoneType:
		return True
	base = typing.get_origin(t)
	if base is None:
		return (t in _scalar_hierarchy or base in _containers)
	else:
		if base not in _scalar_hierarchy and base not in _containers:
			return False
		for arg in typing.get_args(t):
			if not _is_valid_type(arg):
				return False
		return True


def _decompose_type(t: AnyValueType) -> tuple[AnyBaseType, Union[tuple[AnyValueType, ...], None]]:
	base = typing.get_origin(t)
	if base is None:
		return t, None
	else:
		return base, typing.get_args(t)


def _broaden_type(t: AnyValueType, cue: Optional[AnyValueType]=None) -> Union[AnyValueType, None]:
	"""
		`cue` should always come before `t` in `_type_hierarchy`
	"""
	base, type_args = _decompose_type(t)
	if base == str:
		if cue is None:
			return Nullable
		else:
			cue_base, cue_args = _decompose_type(cue)
			if cue_base == Nullable:
				if cue_args is not None and len(cue_args) == 1:
					cue_arg = cast(AnyScalarType, cue_args[0])
					r = Nullable[cue_arg]
					return r
				else:
					return Nullable
			elif cue_base == list:
				return None
			else:
				cue_base = cast(AnyScalarType, cue_base)
				r = Nullable[cue_base]
				return r
	elif base == Nullable:
		if type_args is not None and len(type_args) == 1:
			type_arg = cast(AnyScalarType, type_args[0])
			r = list[type_arg]
			return r
		else:
			if cue is None:
				return list
			else:
				cue_base, cue_args = _decompose_type(cue)
				if cue_base == Nullable:
					r = list[cue]
					return r
				elif cue_base == list:
					return None
				else:
					return list
	elif base == list:
		return None
	else:
		return _scalar_hierarchy[base]


def _merge_types(t1: AnyValueType, t2: AnyValueType) -> AnyValueType:
	if t1 == t2:
		return t1
	if (not _is_valid_type(t1)) or (not _is_valid_type(t2)):
		return GenericValue

	c: Union[AnyValueType, None] = t1
	visited: dict[AnyValueType, Union[tuple[AnyValueType, ...], None]] = {}
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
		if base in visited:
			visited_args = visited[base]
			if type_args is not None and len(type_args) == 1:
				base = cast(AnyContainerBaseType, base)
				type_arg = type_args[0]
				if visited_args is not None and len(visited_args) == 1:
					visited_arg = visited_args[0]
					merged_arg = _merge_types(type_arg, visited_arg)
					r = base[merged_arg]  # type: ignore
					return r
				else:
					r = base[type_arg]  # type: ignore
					return r
			else:
				if visited_args is not None and len(visited_args) == 1:
					base = cast(AnyContainerBaseType, base)  # visited_args were derived from the same base as base, so base must be a container
					visited_arg = visited_args[0]
					r = base[visited_arg]  # type: ignore
					return r
				else:
					return base
		else:
			c = _broaden_type(c, t2)

	return GenericValue


def reduce_types(types: Iterable[AnyValueType]) -> AnyValueType:
	"""
		Reduce multiple types into a single common type.

		If the input types are not all the same, the resulting type will be narrowest possible type that will encompass all of the input types.

		This operation is useful in cases such as parsing a CSV file where each column should have a consistent type, but where the individual values in a column could be interpreted variously as ints or floats (or other types).

		Arguments
		---------
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
	reduced_type: Union[AnyValueType, None] = None
	for t in types:
		if reduced_type is None:
			reduced_type = t
		elif t != reduced_type:
			reduced_type = _merge_types(reduced_type, t)
		if reduced_type == _TerminalValue:
			return _TerminalValue

	if reduced_type is None:
		# types is empty
		return GenericValue
	else:
		return reduced_type
