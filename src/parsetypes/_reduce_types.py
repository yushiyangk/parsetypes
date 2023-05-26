import typing
from decimal import Decimal
from types import NoneType
from typing import Iterable, cast

from ._common import DatumType, GenericDatum, Nullable


_TerminalDatum = list

_type_hierarchy: dict[DatumType, DatumType | None] = {
	bool: int,
	int: Decimal,
	Decimal: float,
	float: str,
	str: Nullable,
	Nullable: list,
	list: None,
}
_containers: set[DatumType] = {Nullable, list}


def _is_valid_type(t: DatumType) -> bool:
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

def _decompose_type(t: DatumType) -> tuple[DatumType, tuple[DatumType, ...] | None]:
	base = typing.get_origin(t)
	if base is None:
		return t, None
	else:
		return cast(DatumType, base), tuple(cast(DatumType, arg) for arg in typing.get_args(t))

def _broaden_type(t: DatumType, cue: DatumType | None=None) -> DatumType | None:
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


def _merge_types(t1: DatumType, t2: DatumType) -> DatumType:
	if t1 == t2:
		return t1
	if (not _is_valid_type(t1)) or (not _is_valid_type(t2)):
		return GenericDatum

	c: DatumType | None = t1
	visited: dict[DatumType, tuple[DatumType, ...] | None] = {}
	if t1 == NoneType:
		visited[NoneType] = None
		visited[Nullable] = None
	else:
		while c is not None:
			base, type_args = _decompose_type(c)
			if base not in visited:
				visited[base] = type_args
			if base == _TerminalDatum:
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

	return GenericDatum

def reduce_types(types: Iterable[DatumType]) -> DatumType:
	reduced_type: DatumType | None = None
	for t in types:
		if reduced_type is None:
			reduced_type = t
		elif t != reduced_type:
			reduced_type = _merge_types(reduced_type, t)
		if reduced_type == _TerminalDatum:
			return _TerminalDatum

	if reduced_type is None:
		return GenericDatum
	else:
		return reduced_type
