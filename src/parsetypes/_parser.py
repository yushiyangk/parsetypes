import math
from decimal import Decimal
from enum import Enum
from typing import Callable, Iterable, Iterator, Optional, Sequence, TypeVar, cast

from ._common import AnyValue, AnyValueType, GenericValue, Nullable
from ._reduce_types import reduce_types, _decompose_type

from ._compat import NoneType, Union


_FloatLike = TypeVar('_FloatLike', float, Decimal)


class _TypeTable:
	__slots__ = ('cols')

	def __init__(self, cols: Union[int, list[list[AnyValueType]]]):
		self.cols: list[list[AnyValueType]]
		if isinstance(cols, int):
			self.cols = [[] for i in range(cols)]
		else:
			self.cols = cols

	def add_row(self, row: Sequence[AnyValueType]):
		if len(row) != len(self.cols):
			raise ValueError(f"incorrect row length: expected {len(self.cols)}, got {len(row)}")
		for i, t in enumerate(row):
			self.cols[i].append(t)


def _decompose_string_pair(string: str, delimiter: str, case_sensitive: bool) -> tuple[str, Union[str, None]]:
	if not case_sensitive:
		delimiter = delimiter.lower()
		operative_string = string.lower()
	else:
		operative_string = string
	if delimiter in operative_string:
		operative_parts = operative_string.split(delimiter)
		if len(operative_parts) != 2:
			return (string, None)
		else:
			delimiter_pos = len(operative_parts[0])
			return (string[:delimiter_pos], string[(delimiter_pos + len(delimiter)):])
	else:
		return (string, None)


class _SpecialValue(Enum):
	# For checking of special values during TypeParser.__init__() only
	LIST = "list delimiter"
	NONE = "None value"
	TRUE = "true value"
	FALSE = "false value"
	INF = "inf value"
	NAN = "nan value"


class TypeParser:
	"""
		A parser that can be used to infer the underlying types of data serialised as strings, and to convert them into their original underlying types.

		The behaviour of the parser and the type inference can be configured either in the constructor or using mutable properties of a parser instance. See the constructor documentation for the list of available options.
	"""

	def __init__(self,
		*,
		trim: bool=True,
		use_decimal: bool=False,
		list_delimiter: Optional[str]=None,
		none_values: Iterable[str]=[""],
		none_case_sensitive: bool=False,
		true_values: Iterable[str]=["true"],
		false_values: Iterable[str]=["false"],
		bool_case_sensitive: bool=False,
		int_case_sensitive: bool=False,
		inf_values: Iterable[str]=[],
		nan_values: Iterable[str]=[],
		float_case_sensitive: bool=False,
		case_sensitive: Optional[bool]=None,
	):
		"""
			Initialise a new parser

			The behaviour of the parser and the type inference can be configured either in the constructor or using mutable properties of a parser instance. For example,

			```python
			parser = TypeParser(list_delimiter=",")
			assert parser.list_delimiter == ","
			parser.list_delimiter = ";"
			assert parser.list_delimiter == ";"
			```

			Keyword arguments
			-----------------
			`trim`
			: whether leading and trailing whitespace should be stripped from strings

			`use_decimal`
			: whether non-integer numeric values should be inferred to be Decimal (exact values) instead of float (non-exact values). Note that this only applies to methods that attempt to infer the type (`infer()` `infer_series()`, `infer_table()`), and does not affect methods where the type is explicitly specified (`is_float()`, `is_decimal()`, `parse_float()`, `parse_decimal()`).

			`list_delimiter`
			: the delimiter used for identifying lists and for separating list items. If set to None, the parser will not attempt to identify lists when inferring types, which usually causes the value to be treated as a str instead. Note that this setting is unaffected by <code><var>parser</var>.trim</code> and <code><var>parser</var>.case_sensitive</code>, and will always be used verbatim.

			`none_values`
			: list of strings that represent the value `None`

			`none_case_sensitive`
			: whether matches against `none_values` should be made in a case-sensitive manner

			`true_values`
			: list of strings that represent the bool value `True`

			`false_values`
			: list of strings that represent the bool value `False`

			`bool_case_sensitive`
			: whether matches against `true_values` and `false_values` should be made in a case-sensitive manner

			`int_case_sensitive`
			: whether checks for int should be done in a case-sensitive manner. This only applies to values given in scientific notation, where the mantissa and exponent usually are separated by `e`.

			`inf_values`
			: list of strings that represent the float or Decimal value of infinity. Each of the strings can also be prepended with a negative sign to represent negative infinity.

			`nan_values`
			: list of strings that represent a float or Decimal that is NaN (not a number)

			`float_case_sensitive`
			: whether checks for float or Decimal should be done in a case-sensitive manner. This applies to matches against `inf_values` and `nan_values`, as well as to values given in scientific notation, where the mantissa and exponent are usually separated by `e`.

			`case_sensitive`
			: whether all matches should be made in a case-sensitive manner. Sets all of `none_case_sensitive`, `bool_case_sensitive`, `int_case_sensitive`, `float_case_sensitive` to the same value, discarding any individual settings.

			Raises
			------
			`ValueError` if any of the options would lead to ambiguities during parsing
		"""

		self._trim: bool = False
		self._use_decimal: bool = False
		self._list_delimiter: Union[str, None] = None
		self._match_none_values: set[str] = set()
		self._original_none_values: set[str] = set()
		self._none_case_sensitive: bool = False
		self._match_true_values: set[str] = set()
		self._original_true_values: set[str] = set()
		self._match_false_values: set[str] = set()
		self._original_false_values: set[str] = set()
		self._bool_case_sensitive: bool = False
		self._int_case_sensitive: bool = False
		self._match_inf_values: set[str] = set()
		self._original_inf_values: set[str] = set()
		self._match_nan_values: set[str] = set()
		self._original_nan_values: set[str] = set()
		self._float_case_sensitive: bool = False

		# Unconfigurable default values
		self._negative_char = "-"
		self._negative_chars = {self._negative_char, "−"}
		self._sign_chars = self._negative_chars | {"+"}
		self._digit_chars = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}  # Because isdigit("²") == True, but int("²") is invalid
		self._digit_separators = {"_"}
		self._scientific_char = "e"
		self._float_separator = "."
		self._reserved_chars = self._sign_chars | self._digit_chars | self._digit_separators | {self._scientific_char} | {self._float_separator}
		# special_chars = self._reserved_chars | self._list_delimiter

		# Configured values

		self.trim = trim
		self.use_decimal = use_decimal
		self.list_delimiter = list_delimiter

		self.none_case_sensitive = none_case_sensitive
		self.bool_case_sensitive = bool_case_sensitive
		self.int_case_sensitive = int_case_sensitive
		self.float_case_sensitive = float_case_sensitive
		self.case_sensitive = case_sensitive

		self.none_values = none_values

		self.true_values = true_values
		self.false_values = false_values

		self.inf_values = inf_values
		self.nan_values = nan_values

		# Check if any special values conflict
		for name, special_values in [
			(_SpecialValue.LIST, [self._list_delimiter] if self._list_delimiter is not None else []),
			(_SpecialValue.NONE, self._match_none_values),
			(_SpecialValue.TRUE, self._match_true_values),
			(_SpecialValue.FALSE, self._match_false_values),
			(_SpecialValue.INF, self._match_inf_values),
			(_SpecialValue.NAN, self._match_nan_values),
		]:
			for special_value in special_values:
				self._validate_special(name, special_value)


	def _validate_special(self, name: _SpecialValue, value: str):
		if value in self._reserved_chars:
			raise ValueError(f"cannot use reserved char as {name.value}: {value}")

		if name != _SpecialValue.NONE and self.is_none(value):
			raise ValueError(f"cannot use None value as {name.value}: {value}")

		if (
			(name == _SpecialValue.TRUE and self.parse_bool(value) != True) or
			(name == _SpecialValue.FALSE and self.parse_bool(value) != False) or
			(name != _SpecialValue.TRUE and name != _SpecialValue.FALSE and self.is_bool(value))
		):
			raise ValueError(f"cannot use bool value as {name.value}: {value}")

		if self.is_int(value):
			raise ValueError(f"cannot use int value as {name.value}: {value}")

		if self._use_decimal:
			if (
				(name == _SpecialValue.INF and self.parse_decimal(value) != Decimal(math.inf)) or
				(name == _SpecialValue.NAN and not self.parse_decimal(value).is_nan()) or
				(name != _SpecialValue.INF and name != _SpecialValue.NAN and self.is_float(value))
			):
				raise ValueError(f"cannot use Decimal value as {name}: {value}")
		else:
			if (
				(name == _SpecialValue.INF and self.parse_float(value) != math.inf) or
				(name == _SpecialValue.NAN and self.parse_float(value) is not math.nan) or
				(name != _SpecialValue.INF and name != _SpecialValue.NAN and self.is_float(value))
			):
				raise ValueError(f"cannot use float value as {name}: {value}")


	@property
	def trim(self) -> bool:
		return self._trim

	@trim.setter
	def trim(self, value: bool):
		if type(value) != bool:
			raise TypeError(f"trim must be a bool: {value}")
		if value != self._trim:
			self._trim = value
			self.none_values = self._original_none_values
			self.true_values = self._original_true_values
			self.false_values = self._original_false_values
			self.inf_values = self._original_inf_values
			self.nan_values = self._original_nan_values


	@property
	def use_decimal(self) -> bool:
		return self._use_decimal

	@use_decimal.setter
	def use_decimal(self, value: bool):
		if type(value) != bool:
			raise TypeError(f"use_decimal must be a bool: {value}")
		self._use_decimal = value


	@property
	def list_delimiter(self) -> Union[str, None]:
		return self._list_delimiter

	@list_delimiter.setter
	def list_delimiter(self, value: Union[str, None]):
		if value is not None and type(value) != str:
			raise TypeError(f"list_delimiter must be a str or None: {value}")
		if value is not None:
			self._validate_special(_SpecialValue.LIST, value)
		self._list_delimiter = value


	@property
	def none_values(self) -> set[str]:
		if self._trim:
			return {value.strip() for value in self._original_none_values}
		else:
			return self._original_none_values

	@none_values.setter
	def none_values(self, values: Iterable[str]):
		if not isinstance(values, Iterable):
			raise TypeError(f"none_values must be an Iterable: {values}")
		for i, value in enumerate(values):
			if type(value) != str:
				raise TypeError(f"each item in none_values must be a str: {value} at index {i}")
		self._original_none_values = set(values)
		if self._trim:
			values = (value.strip() for value in values)
		if not self._none_case_sensitive:
			values = (value.lower() for value in values)
		self._match_none_values = set(values)


	@property
	def none_case_sensitive(self) -> bool:
		return self._none_case_sensitive

	@none_case_sensitive.setter
	def none_case_sensitive(self, value: bool):
		if type(value) != bool:
			raise TypeError(f"none_case_sensitive must be a bool: {value}")
		if value != self._none_case_sensitive:
			self._none_case_sensitive = value
			self.none_values = self._original_none_values


	@property
	def true_values(self) -> set[str]:
		if self._trim:
			return {value.strip() for value in self._original_true_values}
		else:
			return self._original_true_values

	@true_values.setter
	def true_values(self, values: Iterable[str]):
		if not isinstance(values, Iterable):
			raise TypeError(f"true_values must be an Iterable: {values}")
		for i, value in enumerate(values):
			if type(value) != str:
				raise TypeError(f"each item in true_values must be a str: {value} at index {i}")
		self._original_true_values = set(values)
		if self._trim:
			values = (value.strip() for value in values)
		if not self._bool_case_sensitive:
			values = (value.lower() for value in values)
		self._match_true_values = set(values)


	@property
	def false_values(self) -> set[str]:
		if self._trim:
			return {value.strip() for value in self._original_false_values}
		else:
			return self._original_false_values

	@false_values.setter
	def false_values(self, values: Iterable[str]):
		if not isinstance(values, Iterable):
			raise TypeError(f"false_values must be an Iterable: {values}")
		for i, value in enumerate(values):
			if type(value) != str:
				raise TypeError(f"each item in false_values must be a str: {value} at index {i}")
		self._original_false_values = set(values)
		if self._trim:
			values = (value.strip() for value in values)
		if not self._bool_case_sensitive:
			values = (value.lower() for value in values)
		self._match_false_values = set(values)


	@property
	def bool_case_sensitive(self) -> bool:
		return self._bool_case_sensitive

	@bool_case_sensitive.setter
	def bool_case_sensitive(self, value: bool):
		if type(value) != bool:
			raise TypeError(f"bool_case_sensitive must be a bool: {value}")
		if value != self._bool_case_sensitive:
			self._bool_case_sensitive = value
			self.true_values = self._original_true_values
			self.false_values = self._original_false_values


	@property
	def int_case_sensitive(self) -> bool:
		return self._int_case_sensitive

	@int_case_sensitive.setter
	def int_case_sensitive(self, value: bool):
		if type(value) != bool:
			raise TypeError(f"int_case_sensitive must be a bool: {value}")
		self._int_case_sensitive = value


	@property
	def inf_values(self) -> set[str]:
		if self._trim:
			return {value.strip() for value in self._original_inf_values}
		else:
			return self._original_inf_values

	@inf_values.setter
	def inf_values(self, values: Iterable[str]):
		if not isinstance(values, Iterable):
			raise TypeError(f"inf_values must be an Iterable: {values}")
		for i, value in enumerate(values):
			if type(value) != str:
				raise TypeError(f"each item in inf_values must be a str: {value} at index {i}")
		self._original_inf_values = set(values)
		if self._trim:
			values = (value.strip() for value in values)
		if not self._float_case_sensitive:
			values = (value.lower() for value in values)
		self._match_inf_values = set(values)


	@property
	def nan_values(self) -> set[str]:
		values = self._original_nan_values
		if self._trim:
			return {value.strip() for value in self._original_nan_values}
		else:
			return self._original_nan_values

	@nan_values.setter
	def nan_values(self, values: Iterable[str]):
		if not isinstance(values, Iterable):
			raise TypeError(f"nan_values must be an Iterable: {values}")
		for i, value in enumerate(values):
			if type(value) != str:
				raise TypeError(f"each item in nan_values must be a str: {value} at index {i}")
		self._original_nan_values = set(values)
		if self._trim:
			values = (value.strip() for value in values)
		if not self._float_case_sensitive:
			values = (value.lower() for value in values)
		self._match_nan_values = set(values)


	@property
	def float_case_sensitive(self) -> bool:
		return self._float_case_sensitive

	@float_case_sensitive.setter
	def float_case_sensitive(self, value: bool):
		if type(value) != bool:
			raise TypeError(f"float_case_sensitive must be a bool: {value}")
		if value != self._float_case_sensitive:
			self._float_case_sensitive = value
			self.inf_values = self._original_inf_values
			self.nan_values = self._original_nan_values


	@property
	def case_sensitive(self) -> Union[bool, None]:
		if (
			self._none_case_sensitive == self._bool_case_sensitive and
			self._none_case_sensitive == self._int_case_sensitive and
			self._none_case_sensitive == self._float_case_sensitive
		):
			return self._none_case_sensitive
		else:
			return None

	@case_sensitive.setter
	def case_sensitive(self, value: Union[bool, None]):
		if value is not None and type(value) != bool:
			raise TypeError(f"case_sensitive must be a bool or None: {value}")
		if value is not None:
			self.none_case_sensitive = value
			self.int_case_sensitive = value
			self.bool_case_sensitive = value
			self.float_case_sensitive = value


	def is_none(self, value: str) -> bool:
		"""
			Check if a string represents the value None

			Only strings that match the values in <code><var>parser</var>.none_values</code> will be interpreted as None. The default accepted values are `[""]`, i.e. an empty string. The case sensitivity of this matching depends on <code><var>parser</var>.none_case_sensitive</code>, which is False by default.

			Arguments
			---------
			`value`
			: string to be checked

			Returns
			-------
			whether it is None

			Examples
			--------
			```python
			parser = TypeParser()
			parser.is_none("")     # True
			parser.is_none("abc")  # False
			```
		"""
		if self._trim:
			value = value.strip()
		if not self._bool_case_sensitive:
			value = value.lower()

		if value in self._match_none_values:
			return True
		else:
			return False


	def is_bool(self, value: str) -> bool:
		"""
			Check if a string represents a bool

			Only strings that match the values in <code><var>parser</var>.true_values</code> and <code><var>parser</var>.false_values</code> will be interpreted as booleans. The default accepted values are `["true"]` and `["false"]` respectively. The case sensitivity of this matching depends on <code><var>parser</var>.bool_case_sensitive</code>, which is False by default.

			Arguments
			---------
			`value`
			: string to be checked

			Returns
			-------
			whether it is a bool

			Examples
			--------
			```python
			parser = TypeParser()
			parser.is_bool("true")  # True
			parser.is_bool("")      # True
			parser.is_bool("abc")   # False
			```
		"""
		if self._trim:
			value = value.strip()

		if not self._bool_case_sensitive:
			value = value.lower()
		if value in self._match_true_values:
			return True
		if value in self._match_false_values:
			return True

		return False


	def is_int(self, value: str, *, allow_negative: bool=True, allow_sign: bool=True, allow_scientific: bool=True) -> bool:
		"""
			Check if a string represents an int

			Arguments
			---------
			`value`
			: string to be checked

			Keyword arguments
			-----------------

			`allow_negative`
			: whether to accept negative values. Since negative values are always indicated with a negative sign, `allow_sign` must also be True (which is the default setting) for this to have any effect.

			`allow_sign`
			: whether to accept values prepended with a sign character. If False, it implies that `allow_negative` is False also.

			`allow_scientific`
			: whether to accept scientific notation. If True, strings of the form <code>"<var>M</var>e<var>X</var>"</code> will be interpreted as the expression <code><var>M</var> * (10 ** <var>X</var>)</code>, where <var>M</var> is the mantissa/significand and <var>X</var> is the exponent. Note that <var>M</var> must be an integer and <var>X</var> must be a non-negative integer, even in cases where the expression would evaluate mathematically to an integer.

			Returns
			-------
			whether it is an int

			Examples
			--------
			```python
			parser = TypeParser()
			parser.is_int("0")    # True
			parser.is_int("-1")   # True
			parser.is_int("abc")  # False
			parser.is_int("")     # False
			```
		"""
		if self._trim:
			value = value.strip()

		if len(value) == 0:
			return False

		if allow_scientific:
			value, exp = _decompose_string_pair(value, self._scientific_char, self._int_case_sensitive)
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


	def is_float(self, value: str, *, allow_scientific: bool=True, allow_inf: bool=True, allow_nan: bool=True) -> bool:
		"""
			Check if a string represents a float (or equivalently, a Decimal)

			This function will also return True if the string represents an int.

			Alias: `is_decimal()`

			Arguments
			---------
			`value`
			: string to be checked

			Keyword arguments
			-----------------

			`allow_scientific`
			: whether to accept scientific notation. If True, strings of the form <code>"<var>M</var>e<var>X</var>"</code> will be interpreted as the expression <code><var>M</var> * (10 ** <var>X</var>)</code>, where <var>M</var> is the mantissa/significand and <var>X</var> is the exponent. Note that <var>X</var> must be an integer, but can be negative.

			`allow_inf`
			: whether to accept positive and negative infinity values. If True, strings that match the values in <code><var>parser</var>.inf_values</code> (empty set by default) are interpreted as infinity, or as negative infinity if prepended by a negative sign. The case sensitivity of this matching depends on <code><var>parser</var>.float_case_sensitive</code>, which is False by default.

			`allow_nan`
			: whether to accept NaN (not a number) representations. If True, strings that match the values in <code><var>parser</var>.nan_values</code> (empty set by default) are interpeted as NaN. The case sensitivity of this matching also depends on <code><var>parser</var>.float_case_sensitive</code>, which is False by default.

			Returns
			-------
			whether it is a float or Decimal

			Examples
			--------
			```python
			parser = TypeParser()
			parser.is_float("1.")       # True
			parser.is_float("12.3e-2")  # True
			parser.is_float("abc")      # False
			parser.is_float("")         # False
			```
		"""
		if self._trim:
			value = value.strip()

		if len(value) > 0 and value[0] in self._sign_chars:
			value = value[1:]

		if self._float_case_sensitive:
			special_value = value
		else:
			special_value = value.lower()
		if allow_inf and special_value in self._match_inf_values:
			return True
		if allow_nan and special_value in self._match_nan_values:
			return True

		if len(value) == 0:
			return False

		if allow_scientific:
			value, exp = _decompose_string_pair(value, self._scientific_char, self._float_case_sensitive)
			if exp is not None:
				return self.is_float(value, allow_scientific=False, allow_inf=False, allow_nan=False) and self.is_int(exp, allow_sign=True, allow_negative=True, allow_scientific=False)

		value, frac = _decompose_string_pair(value, self._float_separator, self._float_case_sensitive)
		if frac is not None:
			if value == "" and frac == "":
				return False
			return (
				self.is_int(value, allow_sign=True, allow_negative=False, allow_scientific=False) or value == ""
			) and (
				self.is_int(frac, allow_sign=False, allow_negative=False, allow_scientific=False) or frac == ""
			)

		return self.is_int(value, allow_sign=True, allow_negative=True, allow_scientific=False)


	def is_decimal(self, value: str, *, allow_scientific: bool=True, allow_inf: bool=True, allow_nan: bool=True) -> bool:
		"""
			Alias of `is_float()`
		"""
		return self.is_float(value, allow_scientific=allow_scientific, allow_inf=allow_inf, allow_nan=allow_nan)


	def parse_none(self, value: str) -> None:
		"""
			Parse a string and return it as the value None if possible

			Only strings that match the values in <code><var>parser</var>.none_values</code> will be interpreted as None. The default accepted values are `[""]`, i.e. an empty string. The case sensitivity of this matching depends on <code><var>parser</var>.none_case_sensitive</code>, which is False by default.

			Arguments
			---------
			`value`
			: string to be parsed

			Returns
			-------
			parsed None value

			Raises
			------
			`ValueError` if `value` cannot be parsed

			Examples
			--------
			```python
			parser = TypeParser()
			parser.parse_none("")     # None
			parser.parse_none("abc")  # raises ValueError
			```
		"""
		if self.is_none(value):
			return None
		else:
			raise ValueError(f"not a none value: {value}")


	def parse_bool(self, value: str) -> bool:
		"""
			Parse a string and return it as a bool if possible

			Only strings that match the values in <code><var>parser</var>.true_values</code> and <code><var>parser</var>.false_values</code> will be interpreted as booleans. The default accepted values are `["true"]` and `["false"]` respectively. The case sensitivity of this matching depends on <code><var>parser</var>.bool_case_sensitive</code>, which is False by default.

			Arguments
			---------
			`value`
			: string to be parsed

			Returns
			-------
			parsed bool value

			Raises
			------
			`ValueError` if `value` cannot be parsed

			Examples
			--------
			```python
			parser = TypeParser()
			parser.parse_bool("true")   # True
			parser.parse_bool("FALSE")  # False
			```
		"""
		if self._trim:
			value = value.strip()

		if self._bool_case_sensitive:
			special_value = value
		else:
			special_value = value.lower()

		if special_value in self._match_true_values:
			return True
		if special_value in self._match_false_values:
			return False

		raise ValueError(f"not a boolean: {value}")


	def parse_int(self, value: str, *, allow_negative: bool=True, allow_sign: bool=True, allow_scientific: bool=True) -> int:
		"""
			Parse a string and return it as an int if possible

			If the string represents a bool, it will be converted to `1` for True and `0` for False.

			Arguments
			---------
			`value`
			: string to be parsed

			Keyword arguments
			-----------------

			`allow_negative`
			: whether to accept negative values. Since negative values are always indicated with a negative sign, `allow_sign` must also be True (which is the default setting) for this to have any effect.

			`allow_sign`
			: whether to accept values prepended with a sign character. If False, it implies that `allow_negative` is False also.

			`allow_scientific`
			: whether to accept scientific notation. If True, strings of the form <code>"<var>M</var>e<var>X</var>"</code> will be interpreted as the expression <code><var>M</var> * (10 ** <var>X</var>)</code>, where <var>M</var> is the mantissa/significand and <var>X</var> is the exponent. Note that <var>M</var> must be an integer and <var>X</var> must be a non-negative integer, even in cases where the expression would evaluate mathematically to an integer.

			Returns
			-------
			parsed int value

			Raises
			------
			`ValueError` if `value` cannot be parsed

			Examples
			--------
			```python
			parser = TypeParser()
			parser.parse_int("0")    # 0
			parser.parse_int("-1")   # -1
			parser.parse_int("2e3")  # 2000
			```
		"""
		if self._trim:
			value = value.strip()

		if self.is_int(value, allow_negative=allow_negative, allow_sign=allow_sign, allow_scientific=allow_scientific):
			if allow_scientific:
				value, exp = _decompose_string_pair(value, self._scientific_char, self._int_case_sensitive)
				if exp is not None:
					if value[0] in (self._negative_chars - {self._negative_char}):
						value = self._negative_char + value[1:]
					return int(value) * (10 ** int(exp))

			if value[0] in (self._negative_chars - {self._negative_char}):
				value = self._negative_char + value[1:]
			return int(value)

		elif self.is_bool(value):
			return int(self.parse_bool(value))
		else:
			raise ValueError(f"not an integer: {value}")


	def _parse_floatlike(self,
		value: str,
		converter: Callable[[Union[str, bool]], _FloatLike],
		inf_value: _FloatLike,
		nan_value: _FloatLike,
		*,
		allow_scientific: bool=True,
		allow_inf: bool=True,
		allow_nan: bool=True
	) -> _FloatLike:
		if self._trim:
			value = value.strip()
		if self.is_float(value, allow_scientific=allow_scientific, allow_inf=allow_inf, allow_nan=allow_nan):
			if self._float_case_sensitive:
				special_value = value
			else:
				special_value = value.lower()
			if allow_inf and special_value in self._match_inf_values:
				return inf_value
			if allow_nan and special_value in self._match_nan_values:
				return nan_value

			if len(value) > 0 and value[0] in self._sign_chars:
				positive_part = value[1:]
				if self._float_case_sensitive:
					special_value = positive_part
				else:
					special_value = positive_part.lower()
				if allow_inf and special_value in self._match_inf_values:
					if value[0] in self._negative_chars:
						return -1 * inf_value
					else:
						return inf_value
				if allow_nan and special_value in self._match_nan_values:
					return nan_value

				if value[0] in self._negative_chars:
					value = self._negative_char + positive_part
			return converter(value)
		elif self.is_bool(value):
			return converter(self.parse_bool(value))
		else:
			raise ValueError(f"not a {_FloatLike.__name__}: {value}")


	def parse_float(self, value: str, *, allow_scientific: bool=True, allow_inf: bool=True, allow_nan: bool=True) -> float:
		"""
			Parse a string and return it as a (non-exact) float if possible

			If the string represents a bool, it will be converted to `1.` for True and `0.` for False. If the string represents an int, it will be converted to a float also.

			Behaves analogously to `parse_decimal()`, except that that returns an exact Decimal instead.

			Arguments
			---------
			`value`
			: string to be parsed

			Keyword arguments
			-----------------

			`allow_scientific`
			: whether to accept scientific notation. If True, strings of the form <code>"<var>M</var>e<var>X</var>"</code> will be interpreted as the expression <code><var>M</var> * (10 ** <var>X</var>)</code>, where <var>M</var> is the mantissa/significand and <var>X</var> is the exponent. Note that <var>X</var> must be an integer, but can be negative.

			`allow_inf`
			: whether to accept positive and negative infinity values. If True, strings that match the values in <code><var>parser</var>.inf_values</code> (empty set by default) are interpreted as infinity, or as negative infinity if prepended by a negative sign. The case sensitivity of this matching depends on <code><var>parser</var>.float_case_sensitive</code>, which is False by default.

			`allow_nan`
			: whether to accept NaN (not a number) representations. If True, strings that match the values in <code><var>parser</var>.nan_values</code> (empty set by default) are interpeted as NaN. The case sensitivity of this matching also depends on <code><var>parser</var>.float_case_sensitive</code>, which is False by default.

			Returns
			-------
			parsed float value

			Raises
			------
			`ValueError` if `value` cannot be parsed

			Examples
			--------
			```python
			parser = TypeParser(inf_values=["inf"], nan_values=["nan"])
			parser.parse_float("1.")       # 1.
			parser.parse_float("1.23e2")   # 123.
			parser.parse_float("1.23e-2")  # 0.0123
			parser.parse_float("inf")      # math.inf
			```
		"""
		return self._parse_floatlike(value, float, math.inf, math.nan,
			allow_scientific=allow_scientific,
			allow_inf=allow_inf,
			allow_nan=allow_nan,
		)


	def parse_decimal(self, value: str, *, allow_scientific: bool=True, allow_inf: bool=True, allow_nan: bool=True) -> Decimal:
		"""
			Parse a string and return it as an exact Decimal if possible

			If the string represents a bool, it will be converted to `Decimal(1)` for True and `Decimal(0)` for False. If the string represents an int, it will be converted to a Decimal also.

			Behaves analogously to `parse_float()`, except that that returns a non-exact float instead.

			Arguments
			---------
			`value`
			: string to be parsed

			Keyword arguments
			-----------------

			`allow_scientific`
			: whether to accept scientific notation. If True, strings of the form <code>"<var>M</var>e<var>X</var>"</code> will be interpreted as the expression <code><var>M</var> * (10 ** <var>X</var>)</code>, where <var>M</var> is the mantissa/significand and <var>X</var> is the exponent. Note that <var>X</var> must be an integer, but can be negative.

			`allow_inf`
			: whether to accept positive and negative infinity values. If True, strings that match the values in <code><var>parser</var>.inf_values</code> (empty set by default) are interpreted as infinity, or as negative infinity if prepended by a negative sign. The case sensitivity of this matching depends on <code><var>parser</var>.float_case_sensitive</code>, which is False by default.

			`allow_nan`
			: whether to accept NaN (not a number) representations. If True, strings that match the values in <code><var>parser</var>.nan_values</code> (empty set by default) are interpeted as NaN. The case sensitivity of this matching also depends on <code><var>parser</var>.float_case_sensitive</code>, which is False by default.

			Returns
			-------
			parsed Decimal value

			Raises
			------
			`ValueError` if `value` cannot be parsed

			Examples
			--------
			```python
			parser = TypeParser(inf_values=["inf"], nan_values=["nan"])
			parser.parse_decimal("1.")       # Decimal(1)
			parser.parse_decimal("1.23e2")   # Decimal(123)
			parser.parse_decimal("1.23e-2")  # Decimal(123) / Decimal(10000)
			parser.parse_decimal("inf")      # Decimal(math.inf)
			```
		"""
		return self._parse_floatlike(value, Decimal, Decimal(math.inf), Decimal(math.nan),
			allow_scientific=allow_scientific,
			allow_inf=allow_inf,
			allow_nan=allow_nan,
		)


	def infer(self, value: str) -> AnyValueType:
		"""
			Infer the underlying type of a string

			Also check for inline lists if <code><var>parser</var>.list_delimiter</code> is not None.

			Arguments
			---------
			`value`
			: the string for which the type should be inferred

			Returns
			-------
			inferred type

			Examples
			--------
			```python
			parser = TypeParser()
			parser.infer("true")  # bool
			parser.infer("2.0")   # float
			parser.infer("abc")   # str
			```
		"""
		if self.is_none(value):
			return NoneType
		if self.is_bool(value):
			return bool
		if self.is_int(value):
			return int
		if self.is_float(value):
			if self._use_decimal:
				return Decimal
			else:
				return float

		if self._trim:
			value = value.strip()

		if self._list_delimiter is not None and self._list_delimiter in value:
			subvalues = value.split(self._list_delimiter)
			if self._trim:
				subvalues = [subvalue.strip() for subvalue in subvalues]
			reduced_type = reduce_types(self.infer(subvalue) for subvalue in subvalues)
			r = list[reduced_type]
			return r

		return GenericValue


	def infer_series(self, values: Iterable[str]) -> AnyValueType:
		"""
			Infer the underlying common type of a series of strings

			If the values in the series do not have the same apparent type, the resulting type will be narrowest possible type that will encompass all values in the series. See `parsetypes.reduce_types()` for more information.

			Arguments
			---------
			`values`
			: series of strings for which the type should be inferred

			Returns
			-------
			inferred type

			Examples
			--------
			```python
			parser = TypeParser()
			parser.infer_series(["1", "2", "3.4"])       # float
			parser.infer_series(["true", "false", "2"])  # int
			parser.infer_series(["1", "2.3", "abc"])     # str
			```
		"""
		return reduce_types(self.infer(value) for value in values)


	def infer_table(self, rows: Iterable[Sequence[str]]) -> list[AnyValueType]:
		"""
			Infer the underlying common type for each column of a table of strings

			For each column, if the values do not have the same apparent type, the resulting type will be narrowest possible type that will encompass all values in the column. See `parsetypes.reduce_types()` for more information.

			Note that the individual inferred types of every value in the table must be able to fit into memory.

			Arguments
			---------
			`rows`
			: table of strings for which the types should be inferred, in row-major order

			Returns
			-------
			inferred types

			Examples
			--------
			```python
			parser = TypeParser()
			parser.infer_table([
				["1",   "true",  "1"],
				["2",   "false", "2.3"],
				["3.4", "2",     "abc"],
			])
			# [float, int, str]
			```
		"""
		rows_iter = iter(rows)
		first_row = next(rows_iter, None)
		if first_row is None:
			return []

		num_cols = len(first_row)
		if num_cols == 0:
			return []

		table = _TypeTable([[self.infer(value)] for value in first_row])
		for row in rows_iter:
			table.add_row([self.infer(value) for value in row])

		return [reduce_types(col) for col in table.cols]


	def convert(self, value: str, target_type: AnyValueType) -> AnyValue:
		"""
			Convert a string to the specified target type if possible

			Valid values for `target_type` include any return value from `infer()`, `infer_series()` and `infer_table()`. To infer and convert the string automatically, use `parse()`, `parse_series()` or `parse_table()` instead.

			Arguments
			---------
			`value`
			: the string to be converted

			`target_type`
			: type to which the value should be converted

			Returns
			-------
			converted value

			Raises
			-------
			`ValueError`
			: if `value` cannot be converted to `target_type`

			`TypeError`
			: if `target_type` is not a valid type

			Examples
			--------
			```python
			parser = TypeParser()
			parser.convert("true", bool)  # True
			parser.convert("2", int)      # 2
			parser.convert("2", float)    # 2.
			```
		"""
		base, type_args = _decompose_type(target_type)
		if base == NoneType:
			return self.parse_none(value)
		elif base == bool:
			return self.parse_bool(value)
		elif base == int:
			return self.parse_int(value)
		elif base == Decimal:
			return self.parse_decimal(value)
		elif base == float:
			return self.parse_float(value)
		elif base == str:
			return value
		elif base == Nullable:
			if self.is_none(value):
				return None
			else:
				if type_args is not None and len(type_args) == 1 and type_args[0] != str:
					inner_type = type_args[0]
					return self.convert(value, inner_type)
				else:
					return value
		elif base == list:
			subvalues = value.split(self._list_delimiter)
			if self._trim:
				subvalues = [subvalue.strip() for subvalue in subvalues]
			if type_args is not None and len(type_args) == 1 and type_args[0] != str:
				subtype = type_args[0]
				return [self.convert(subvalue, subtype) for subvalue in subvalues]
			else:
				return subvalues
		else:
			raise TypeError(f"cannot convert to type: {target_type}")


	def parse(self, value: str) -> AnyValue:
		"""
			Parse a string and convert it to its underlying type

			Arguments
			---------
			`value`
			: the string to be parsed

			Returns
			-------
			converted value

			Examples
			--------
			```python
			parser = TypeParser()
			parser.parse("true")  # True
			parser.parse("2.0")   # 2.
			parser.parse("abc")   # "abc"
			```
		"""
		return self.convert(value, self.infer(value))


	def parse_series(self, values: Iterable[str]) -> list[AnyValue]:
		"""
			Parse a series of strings and convert them to their underlying common type

			If the values in the series do not have the same apparent type, the common type is taken as the narrowest possible type that will encompass all values in the series. See `parsetypes.reduce_types()` for more information.

			Arguments
			---------
			`values`
			: series of strings to be parsed

			Returns
			-------
			converted values

			Examples
			--------
			```python
			parser = TypeParser()
			parser.parse_series(["1", "2", "3"])        # [1, 2, 3]
			parser.parse_series(["5", "6.7", "8."])     # [5., 6.7, 8.]
			parser.parse_series(["true", "false", ""])  # [True, False, None]
			parser.parse_series(["1", "2.3", "abc"])    # ["1", "2.3", "abc"]
			```
		"""
		inferred = self.infer_series(values)
		return [self.convert(value, inferred) for value in values]


	def parse_table(self, rows: Iterable[Sequence[str]]) -> list[list[AnyValue]]:
		"""
			Parse a table of strings and convert them to the underlying common type of each column

			For each column, if the values do not have the same apparent type, the common type is taken as the narrowest possible type that will encompass all values in the column. See `parsetypes.reduce_types()` for more information.

			Note that the type to which the values should be converted is determined by `infer_table()`, and so the individual inferred types of every value in the table must be able to fit into memory.

			This is a function that computes the entire table and returns it all at once. The generator function `iterate_table()` behaves analogously, except that it computes and yields each row one at a time instead.

			Arguments
			---------
			`rows`
			: table of strings to be parsed, in row-major order

			`iterator`
			: whether the parsed values should be yielded as an iterator. If False, which is the default, the entire table is computed and returned as a list of lists. If True, this function behaves as a generator, and the rows of the table are computed and yielded one at a time. However, note that even when set to True, the type inference requires that inferred type of each individual value must all be able to fit into memory at once.

			Returns
			-------
			converted table of values, in row-major order

			Examples
			--------
			```python
			parser = TypeParser()
			table = parser.parse_table([
				["1", "5",   "true",  "1"],
				["2", "6.7", "false", "2.3"],
				["3", "8.0", "",      "abc"],
			]):
			assert table == [
				[1, 5.,  True,  "1"],
				[2, 6.7, False, "2.3"],
				[3, 8.,  None,  "abc"],
			]
			```
		"""
		return [converted_row for converted_row in self.iterate_table(rows)]


	def iterate_table(self, rows: Iterable[Sequence[str]]) -> Iterator[list[AnyValue]]:
		"""
			Parse a table of strings for the underlying common type of each column, then convert and yield each row

			For each column, if the values do not have the same apparent type, the common type is taken as the narrowest possible type that will encompass all values in the column. See `parsetypes.reduce_types()` for more information.

			This is a generator function that computes and yields each row one at a time. However, note that in order to determine the types to which each column should be converted, the individual inferred types of every value in the table must still be able to fit into memory.

			The function `parse_table()` behaves analogously, except that it computes the entire table and returns it as a list of lists instead.

			Arguments
			---------
			`rows`
			: table of strings to be parsed, in row-major order

			Yields
			------
			each row of converted table values

			Examples
			--------
			```python
			parser = TypeParser()
			table = parser.iterate_table([
				["1",   "true",  "1"],
				["2",   "false", "2.3"],
				["3.4", "2",     "abc"],
			]):
			assert next(table) == [1.,  1, "1"]
			assert next(table) == [2.,  0, "2.3"]
			assert next(table) == [3.4, 2, "abc"]
			```
		"""
		inferred_types = self.infer_table(rows)

		for row in rows:
			yield [self.convert(value, inferred) for value, inferred in zip(row, inferred_types)]
