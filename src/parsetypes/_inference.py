from __future__ import annotations

import math
import typing
from decimal import Decimal
from enum import Enum
from types import NoneType
from typing import Callable, Iterable, Sequence, Type, TypeVar, cast, Optional, Union

from ._common import Datum, DatumType, GenericDatum, Nullable, Scalar


_FloatLike = TypeVar('_FloatLike', float, Decimal)


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


class _TypeTable:
	__slots__ = ('cols')

	def __init__(self, cols: int | list[list[DatumType]]):
		self.cols: list[list[DatumType]]
		if isinstance(cols, int):
			self.cols = [[] for i in range(cols)]
		else:
			self.cols = cols

	def add_row(self, row: Sequence[DatumType]):
		if len(row) != len(self.cols):
			raise ValueError(f"incorrect row length: expected {len(self.cols)}, got {len(row)}")
		for i, t in enumerate(row):
			self.cols[i].append(t)


def _decompose_string_pair(string: str, delimiter: str) -> tuple[str, str | None]:
	lower_string = string.lower()
	if delimiter in lower_string:
		parts = lower_string.split(delimiter)
		if len(parts) != 2:
			return (string, None)
		else:
			return (parts[0], parts[1])
	else:
		return (string, None)


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


class _SpecialValue(Enum):
	LIST = "list delimiter"
	NONE = "None value"
	TRUE = "true value"
	FALSE = "false value"
	INF = "inf value"
	NAN = "nan value"


# TODO: implement use_decimal and add tests, but tsch should set use_decimal=True
class Inferrer:
	def __init__(self, *,
		trim: bool=True,
		list_delimiter: str | None=None,
		none_values: Iterable[str]=[""],
		none_case_sensitive: bool=False,
		true_values: Iterable[str]=["true"],
		false_values: Iterable[str]=["false"],
		bool_case_sensitive: bool=False,
		inf_values: Iterable[str]=[],
		nan_values: Iterable[str]=[],
		float_case_sensitive: bool=False,
		case_sensitive: bool | None=None,
	):
		if case_sensitive is not None:
			none_case_sensitive = case_sensitive
			bool_case_sensitive = case_sensitive
			float_case_sensitive = case_sensitive

		# TODO: Check if listdelimiter is in special values or any character used by int/float
		# set reserved characters
		# simply check each special value against all the is_* during __init__, which solves the problem in general

		self.trim = trim
		if self.trim:
			none_values = (value.strip() for value in none_values)
			true_values = (value.strip() for value in true_values)
			false_values = (value.strip() for value in false_values)
			inf_values = (value.strip() for value in inf_values)
			nan_values = (value.strip() for value in nan_values)

		self.list_delimiter = list_delimiter

		self.none_case_sensitive = none_case_sensitive
		if not self.none_case_sensitive:
			none_values = (value.lower() for value in none_values)
		self.none_values = set(none_values)

		self.bool_case_sensitive = bool_case_sensitive
		if not self.bool_case_sensitive:
			true_values = (value.lower() for value in true_values)
			false_values = (value.lower() for value in false_values)
		self.true_values = set(true_values)
		self.false_values = set(false_values)

		self.float_case_sensitive = float_case_sensitive
		if not self.float_case_sensitive:
			inf_values = (value.lower() for value in inf_values)
			nan_values = (value.lower() for value in nan_values)
		self.inf_values = set(inf_values)
		self.nan_values = set(nan_values)

		# Unconfigurable default values
		self._negative_char = "-"
		self._negative_chars = {self._negative_char, "−"}
		self._sign_chars = self._negative_chars | {"+"}
		self._digit_chars = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}  # Because isdigit("²") == True, but int("²") is invalid
		self._digit_separators = {"_"}
		self._scientific_char = "e"
		self._float_separator = "."
		self._reserved_chars = self._sign_chars | self._digit_chars | self._digit_separators | {self._scientific_char} | {self._float_separator}
		# special_chars = self._reserved_chars | self.list_delimiter

		# Check if any special values conflict
		for name, special_values in [
			(_SpecialValue.LIST, [self.list_delimiter] if self.list_delimiter is not None else []),
			(_SpecialValue.NONE, self.none_values),
			(_SpecialValue.TRUE, self.true_values),
			(_SpecialValue.FALSE, self.false_values),
			(_SpecialValue.INF, self.inf_values),
			(_SpecialValue.NAN, self.nan_values),
		]:
			for special_value in special_values:
				if special_value in self._reserved_chars:
					raise ValueError(f"cannot use reserved char as {name.value}: {special_value}")

				if name != _SpecialValue.NONE and self.is_none(special_value):
					raise ValueError(f"cannot use None value as {name.value}: {special_value}")

				if (
					(name == _SpecialValue.TRUE and self.to_bool(special_value) != True) or
					(name == _SpecialValue.FALSE and self.to_bool(special_value) != False) or
					(name != _SpecialValue.TRUE and name != _SpecialValue.FALSE and self.is_bool(special_value))
				):
					raise ValueError(f"cannot use bool value as {name.value}: {special_value}")

				if self.is_int(special_value):
					raise ValueError(f"cannot use int value as {name.value}: {special_value}")

				if (
					(name == _SpecialValue.INF and self.to_float(special_value) != math.inf) or
					(name == _SpecialValue.NAN and self.to_float(special_value) is not math.nan) or
					(name != _SpecialValue.INF and name != _SpecialValue.NAN and self.is_float(special_value))
				):
					raise ValueError(f"cannot use float or Decimal value as {name}: {special_value}")


	def is_none(self, value: str) -> bool:
		"""
			Check if the string represents None.
		"""
		if self.trim:
			value = value.strip()
		if not self.bool_case_sensitive:
			value = value.lower()

		if value in self.none_values:
			return True
		else:
			return False


	def to_none(self, value: str) -> None:
		"""
			Convert a string to None if possible, or raise ValueError otherwise.
		"""
		if self.is_none(value):
			return None
		else:
			raise ValueError(f"not a none value: {value}")


	def is_bool(self, value: str) -> bool:
		"""
			Check if the string represents a bool.
		"""
		if self.trim:
			value = value.strip()

		if not self.bool_case_sensitive:
			value = value.lower()
		if value in self.true_values:
			return True
		if value in self.false_values:
			return True

		return False


	def to_bool(self, value: str) -> bool:
		"""
			Convert a string to a bool if possible, or raise ValueError otherwise.
		"""
		if self.trim:
			value = value.strip()

		if self.bool_case_sensitive:
			special_value = value
		else:
			special_value = value.lower()
		if special_value in self.true_values:
			return True
		if special_value in self.false_values:
			return False

		raise ValueError(f"not a boolean: {value}")


	def is_int(self, value: str, *, allow_sign: bool=True, allow_negative: bool=True, allow_scientific: bool=True) -> bool:
		"""
			Check if the string represents an int.
		"""
		if self.trim:
			value = value.strip()

		if len(value) == 0:
			return False

		if allow_scientific:
			value, exp = _decompose_string_pair(value, self._scientific_char)
			if exp is not None:
				return self.is_int(
					value, allow_sign=True, allow_negative=allow_negative, allow_scientific=False
				) and self.is_int(
					exp, allow_sign=True, allow_negative=False, allow_scientific=False
				)

		if value[0] in self._sign_chars:
			if len(value) == 1:
				return False
			if not allow_sign:
				return False
			if not allow_negative and value[0] in self._negative_chars:
				return False
			value = value[1:]
		if value[0] in self._digit_separators or value[-1] in self._digit_separators:
			return False

		prev_separated = False
		for c in value:
			if c in self._digit_separators:
				if prev_separated:
					return False
				prev_separated = True
			else:
				prev_separated = False
				if c not in self._digit_chars:
					return False
		return True


	def to_int(self, value: str, *, allow_scientific: bool=True) -> int:
		"""
			Convert a string to an int if possible, or raise ValueError otherwise.
		"""
		if self.trim:
			value = value.strip()

		if self.is_int(value, allow_sign=True, allow_negative=True, allow_scientific=allow_scientific):
			if allow_scientific:
				value, exp = _decompose_string_pair(value, self._scientific_char)
				if exp is not None:
					if value[0] in (self._negative_chars - {self._negative_char}):
						value = self._negative_char + value[1:]
					return int(value) * (10 ** int(exp))

			if value[0] in (self._negative_chars - {self._negative_char}):
				value = self._negative_char + value[1:]
			return int(value)

		else:
			raise ValueError(f"not an integer: {value}")


	def is_float(self, value: str, *, allow_scientific: bool=True, allow_inf: bool=True, allow_nan: bool=True) -> bool:
		"""
			Check if the string represents a float.
		"""
		if self.trim:
			value = value.strip()

		if len(value) > 0 and value[0] in self._sign_chars:
			value = value[1:]

		if self.float_case_sensitive:
			special_value = value
		else:
			special_value = value.lower()
		if allow_inf and special_value in self.inf_values:
			return True
		if allow_nan and special_value in self.nan_values:
			return True

		if len(value) == 0:
			return False

		if allow_scientific:
			value, exp = _decompose_string_pair(value, self._scientific_char)
			if exp is not None:
				return self.is_float(value, allow_scientific=False, allow_inf=False, allow_nan=False) and self.is_int(exp, allow_sign=True, allow_negative=True, allow_scientific=False)

		value, frac = _decompose_string_pair(value, self._float_separator)
		if frac is not None:
			if value == "" and frac == "":
				return False
			return (
				self.is_int(value, allow_sign=True, allow_negative=False, allow_scientific=False) or value == ""
			) and (
				self.is_int(frac, allow_sign=False, allow_negative=False, allow_scientific=False) or frac == ""
			)

		return self.is_int(value, allow_sign=True, allow_negative=True, allow_scientific=False)


	def _to_floatlike(self,
		value: str,
		converter: Callable[[str], _FloatLike],
		inf_value: _FloatLike,
		nan_value: _FloatLike,
		*,
		allow_scientific: bool=True,
		allow_inf: bool=True,
		allow_nan: bool=True
	) -> _FloatLike:
		if self.trim:
			value = value.strip()
		if self.is_float(value, allow_scientific=allow_scientific, allow_inf=allow_inf, allow_nan=allow_nan):
			if self.float_case_sensitive:
				special_value = value
			else:
				special_value = value.lower()
			if allow_inf and special_value in self.inf_values:
				return inf_value
			if allow_nan and special_value in self.nan_values:
				return nan_value

			if len(value) > 0 and value[0] in self._sign_chars:
				positive_part = value[1:]
				if self.float_case_sensitive:
					special_value = positive_part
				else:
					special_value = positive_part.lower()
				if allow_inf and special_value in self.inf_values:
					if value[0] in self._negative_chars:
						return -1 * inf_value
					else:
						return inf_value
				if allow_nan and special_value in self.nan_values:
					return nan_value

				if value[0] in self._negative_chars:
					value = self._negative_char + positive_part
			return converter(value)
		else:
			raise ValueError(f"not a {_FloatLike.__name__}: {value}")


	def to_float(self, value: str, *, allow_scientific: bool=True, allow_inf: bool=True, allow_nan: bool=True) -> float:
		"""
			Convert a string to a (non-exact) float if possible, or raise ValueError otherwise.
		"""
		return self._to_floatlike(value, float, math.inf, math.nan,
			allow_scientific=allow_scientific,
			allow_inf=allow_inf,
			allow_nan=allow_nan,
		)


	def is_decimal(self, value: str, *, allow_scientific: bool=True, allow_inf: bool=True, allow_nan: bool=True) -> bool:
		"""
			Alias of `is_float()`.
		"""
		return self.is_float(value, allow_scientific=allow_scientific, allow_inf=allow_inf, allow_nan=allow_nan)


	def to_decimal(self, value: str, *, allow_scientific: bool=True, allow_inf: bool=True, allow_nan: bool=True) -> Decimal:
		"""
			Convert a string to an exact Decimal if possible, or raise ValueError otherwise.
		"""
		return self._to_floatlike(value, Decimal, Decimal(math.inf), Decimal(math.nan),
			allow_scientific=allow_scientific,
			allow_inf=allow_inf,
			allow_nan=allow_nan,
		)


	def infer_type(self, value: str) -> DatumType:
		"""
			Infer the type of value given as a string.

			Also check for inline lists if `self.list_delimiter` is not None.
		"""
		if self.is_none(value):
			return NoneType
		if self.is_bool(value):
			return bool
		if self.is_int(value):
			return int
		if self.is_float(value):
			return Decimal

		if self.trim:
			value = value.strip()

		if self.list_delimiter is not None and self.list_delimiter in value:
			subvalues = value.split(self.list_delimiter)
			print(subvalues)
			if self.trim:
				subvalues = [subvalue.strip() for subvalue in subvalues]
			return list[reduce_types(self.infer_type(subvalue) for subvalue in subvalues)]

		return str


	def infer_table_types(self, rows: Iterable[Sequence[str]]) -> list[DatumType]:
		"""
			Infer the type of each column for a table of strings.
		"""
		rows_iter = iter(rows)
		first_row = next(rows_iter, None)
		if first_row is None:
			return []

		num_cols = len(first_row)
		if num_cols == 0:
			return []

		table = _TypeTable([[self.infer_type(value)] for value in first_row])
		for row in rows_iter:
			table.add_row([self.infer_type(value) for value in row])

		return [reduce_types(col) for col in table.cols]
