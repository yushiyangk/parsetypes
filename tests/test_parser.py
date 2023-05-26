from __future__ import annotations

import math
from decimal import Decimal
from types import NoneType
from unittest.mock import call, patch

import pytest

from parsetypes import DatumType, TypeParser, Nullable


@pytest.fixture
def default_inferrer():
	return TypeParser()


class TestNull:
	@staticmethod
	@pytest.mark.parametrize(
		('value', 'is_none_expected'),
		[
			("", True),
			("None", False),
			("none", False),
		]
	)
	def test_default(default_inferrer: TypeParser, value: str, is_none_expected: bool):
		is_none_result = default_inferrer.is_none(value)
		assert is_none_result == is_none_expected

		if is_none_expected:
			result = default_inferrer.to_none(value)
			assert result is None
		else:
			with pytest.raises(ValueError):
				default_inferrer.to_bool(value)


	@staticmethod
	@pytest.fixture
	def none_values_inferrer(request: pytest.FixtureRequest) -> TypeParser:
		return TypeParser(none_values=request.param)

	no_values = []
	empty_str_none = [""]
	none_values = ["none", " nil \n"]

	@staticmethod
	@pytest.mark.parametrize(
		('value', 'none_values_inferrer', 'is_none_expected'),
		[
			("none", none_values, True),
			("NONE", none_values, True),
			("nil", none_values, True),
			("NiL", none_values, True),
			("n", none_values, False),
			("", none_values, False),
			("true", none_values, False),
			("1", none_values, False),

			("none", no_values, False),
			("", no_values, False),
			("true", no_values, False),
			("1", no_values, False),
		],
		indirect=['none_values_inferrer']
	)
	def test_none_values(
		value: str,
		none_values_inferrer: TypeParser,
		is_none_expected: bool,
	):
		is_none_result = none_values_inferrer.is_none(value)
		assert is_none_result == is_none_expected

		if is_none_expected:
			result = none_values_inferrer.to_none(value)
			assert result is None
		else:
			with pytest.raises(ValueError):
				none_values_inferrer.to_none(value)


	@staticmethod
	@pytest.fixture
	def none_trim_inferrer(request: pytest.FixtureRequest) -> TypeParser:
		return TypeParser(trim=request.param[0], none_values=request.param[1])

	@staticmethod
	@pytest.mark.parametrize(
		('value', 'none_trim_inferrer', 'is_none_expected'),
		[
			("none", (True, none_values), True),
			(" none \n", (True, none_values), True),
			("nil", (True, none_values), True),
			(" nil \n", (True, none_values), True),
			("", (True, none_values), False),
			("true", (True, none_values), False),
			("1", (True, none_values), False),

			("none", (False, none_values), True),
			(" none \n", (False, none_values), False),
			("nil", (False, none_values), False),
			(" nil \n", (False, none_values), True),
			("", (False, none_values), False),
			("true", (False, none_values), False),
			("1", (False, none_values), False),

			("", (True, empty_str_none), True),
			(" ", (True, empty_str_none), True),
			(" \n", (True, empty_str_none), True),
			("", (False, empty_str_none), True),
			(" ", (False, empty_str_none), False),
			(" \n", (False, empty_str_none), False),
		],
		indirect=['none_trim_inferrer']
	)
	def test_trim(
		value: str,
		none_trim_inferrer: TypeParser,
		is_none_expected: bool,
	):
		is_none_result = none_trim_inferrer.is_none(value)
		assert is_none_result == is_none_expected

		if is_none_expected:
			result = none_trim_inferrer.to_none(value)
			assert result is None
		else:
			with pytest.raises(ValueError):
				none_trim_inferrer.to_none(value)


class TestBool:
	@staticmethod
	@pytest.mark.parametrize(
		('value', 'is_bool_expected', 'expected_bool'),
		[
			("true", True, True),
			("TRUE", True, True),
			("tRuE", True, True),
			("false", True, False),
			("FALSE", True, False),
			("fAlSe", True, False),
			("t", False, None),
			("T", False, None),
			("f", False, None),
			("F", False, None),
			("a", False, None),
			("1", False, None),
			("", False, None),
		]
	)
	def test_default(default_inferrer: TypeParser, value: str, is_bool_expected: bool, expected_bool: bool | None):
		is_bool_result = default_inferrer.is_bool(value)
		assert is_bool_result == is_bool_expected

		if expected_bool is None:
			with pytest.raises(ValueError):
				default_inferrer.to_bool(value)
		else:
			result = default_inferrer.to_bool(value)
			assert result == expected_bool


	@staticmethod
	@pytest.fixture
	def bool_values_inferrer(request: pytest.FixtureRequest) -> TypeParser:
		return TypeParser(true_values=request.param[0], false_values=request.param[1], none_values=[])

	no_values = ([], [])
	empty_str_true = ([""], [])
	bool_values = (["t", " tru \n"], ["FA", " NEG \n"])

	@staticmethod
	@pytest.mark.parametrize(
		('value', 'bool_values_inferrer', 'is_bool_expected', 'expected_bool'),
		[
			("t", bool_values, True, True),
			("T", bool_values, True, True),
			("tru", bool_values, True, True),
			("tRu", bool_values, True, True),
			("tr", bool_values, False, None),
			("true", bool_values, False, None),
			("fa", bool_values, True, False),
			("FA", bool_values, True, False),
			("neg", bool_values, True, False),
			("NEG", bool_values, True, False),
			("f", bool_values, False, None),
			("true", bool_values, False, None),
			("1", bool_values, False, None),
			("", bool_values, False, None),

			("true", no_values, False, None),
			("false", no_values, False, None),
			("", no_values, False, None),

			("", empty_str_true, True, True),
			("false", empty_str_true, False, None),
		],
		indirect=['bool_values_inferrer']
	)
	def test_bool_values(
		value: str,
		bool_values_inferrer: TypeParser,
		is_bool_expected: bool,
		expected_bool: bool | None
	):
		is_bool_result = bool_values_inferrer.is_bool(value)
		assert is_bool_result == is_bool_expected

		if expected_bool is None:
			with pytest.raises(ValueError):
				bool_values_inferrer.to_bool(value)
		else:
			result = bool_values_inferrer.to_bool(value)
			assert result == expected_bool


	@staticmethod
	@pytest.fixture
	def bool_case_sensitive_inferrer(request: pytest.FixtureRequest) -> TypeParser:
		return TypeParser(bool_case_sensitive=request.param[0], true_values=request.param[1], false_values=request.param[2])

	@staticmethod
	@pytest.mark.parametrize(
		('value', 'bool_case_sensitive_inferrer', 'is_bool_expected', 'expected_bool'),
		[
			("tru", (False, *bool_values), True, True),
			("TRU", (False, *bool_values), True, True),
			("TrU", (False, *bool_values), True, True),
			("neg", (False, *bool_values), True, False),
			("NEG", (False, *bool_values), True, False),
			("nEg", (False, *bool_values), True, False),
			("true", (False, *bool_values), False, None),
			("false", (False, *bool_values), False, None),

			("tru", (True, *bool_values), True, True),
			("TRU", (True, *bool_values), False, None),
			("TrU", (True, *bool_values), False, None),
			("neg", (True, *bool_values), False, None),
			("NEG", (True, *bool_values), True, False),
			("nEg", (True, *bool_values), False, None),
			("true", (True, *bool_values), False, None),
			("false", (True, *bool_values), False, None),
		],
		indirect=['bool_case_sensitive_inferrer']
	)
	def test_case_sensitive(
		value: str,
		bool_case_sensitive_inferrer: TypeParser,
		is_bool_expected: bool,
		expected_bool: bool | None
	):
		is_bool_result = bool_case_sensitive_inferrer.is_bool(value)
		assert is_bool_result == is_bool_expected

		if expected_bool is None:
			with pytest.raises(ValueError):
				bool_case_sensitive_inferrer.to_bool(value)
		else:
			result = bool_case_sensitive_inferrer.to_bool(value)
			assert result == expected_bool


	@staticmethod
	@pytest.fixture
	def bool_trim_inferrer(request: pytest.FixtureRequest) -> TypeParser:
		return TypeParser(trim=request.param[0], true_values=request.param[1], false_values=request.param[2], none_values=[])

	@staticmethod
	@pytest.mark.parametrize(
		('value', 'bool_trim_inferrer', 'is_bool_expected', 'expected_bool'),
		[
			("tru", (True, *bool_values), True, True),
			(" tru \n", (True, *bool_values), True, True),
			("neg", (True, *bool_values), True, False),
			(" neg \n", (True, *bool_values), True, False),
			("true", (True, *bool_values), False, None),
			("false", (True, *bool_values), False, None),

			("tru", (False, *bool_values), False, None),
			(" tru \n", (False, *bool_values), True, True),
			("neg", (False, *bool_values), False, None),
			(" neg \n", (False, *bool_values), True, False),
			("true", (False, *bool_values), False, None),
			("false", (False, *bool_values), False, None),

			("", (True, *empty_str_true), True, True),
			(" ", (True, *empty_str_true), True, True),
			(" \n", (True, *empty_str_true), True, True),
			("", (False, *empty_str_true), True, True),
			(" ", (False, *empty_str_true), False, None),
			(" \n", (False, *empty_str_true), False, None),
		],
		indirect=['bool_trim_inferrer']
	)
	def test_trim(
		value: str,
		bool_trim_inferrer: TypeParser,
		is_bool_expected: bool,
		expected_bool: bool | None,
	):
		is_bool_result = bool_trim_inferrer.is_bool(value)
		assert is_bool_result == is_bool_expected

		if expected_bool is None:
			with pytest.raises(ValueError):
				bool_trim_inferrer.to_bool(value)
		else:
			result = bool_trim_inferrer.to_bool(value)
			assert result == expected_bool


class TestInt:
	int_test_cases = [
		("0", True, 0),
		("1", True, 1),
		("20", True, 20),
		("03", True, 3),
		("4_0", True, 40),
		("1_000_000_0_0_0", True, 10 ** 9),
		("_10", False, None),
		("1000_", False, None),
		("1__0", False, None),
		("1_000_000__0", False, None),
		("a", False, None),
		("2b", False, None),
		("c3", False, None),
		("4d4", False, None),
		("e5e", False, None),
		("e5e", False, None),
		("½", False, None),
		("¹", False, None),
		("²", False, None),
		("³", False, None),
		("⁴", False, None),
		("₅", False, None),
		("", False, None),
	]

	not_int_test_cases = [
		("1.0", False, None),
		("0.", False, None),
		("1.", False, None),
		("0.1", False, None),
		(".1", False, None),
	]


	@staticmethod
	@pytest.mark.parametrize(('value', 'is_int_expected', 'expected_int'), int_test_cases + not_int_test_cases)
	def test_default(default_inferrer: TypeParser, value: str, is_int_expected: bool, expected_int: int | None):
		is_int_result = default_inferrer.is_int(value)
		assert is_int_result == is_int_expected

		if expected_int is None:
			with pytest.raises(ValueError):
				default_inferrer.to_int(value)
		else:
			result = default_inferrer.to_int(value)
			assert result == expected_int


	@staticmethod
	@pytest.mark.parametrize(
		('value', 'is_int_allow_sign_expected', 'is_int_allow_negative_expected', 'is_int_allow_both_expected', 'expected_int'),
		# All test cases expect False when both disallowed
		[
			("+0", True, False, True, 0),
			("-0", False, False, True, 0),
			("−0", False, False, True, 0),
			("+1", True, False, True, 1),
			("+20", True, False, True, 20),
			("+03", True, False, True, 3),
			("-4", False, False, True, -4),
			("-50", False, False, True, -50),
			("-06", False, False, True, -6),
			("−7", False, False, True, -7),
			("−80", False, False, True, -80),
			("−09", False, False, True, -9),
			("++10", False, False, False, None),
			("--10", False, False, False, None),
			("10+", False, False, False, None),
			("10-", False, False, False, None),
			("1+1", False, False, False, None),
			("1-1", False, False, False, None),
			("0+1", False, False, False, None),
			("0-1", False, False, False, None),
		]
	)
	def test_allow_sign_negative(
		default_inferrer: TypeParser,
		value: str,
		is_int_allow_sign_expected: bool,
		is_int_allow_negative_expected: bool,
		is_int_allow_both_expected: bool,
		expected_int: int
	):
		is_int_allow_sign_result = default_inferrer.is_int(value, allow_sign=True, allow_negative=False)
		assert is_int_allow_sign_result == is_int_allow_sign_expected
		is_int_allow_negative_result = default_inferrer.is_int(value, allow_sign=False, allow_negative=True)
		assert is_int_allow_negative_result == is_int_allow_negative_expected
		is_int_allow_both_result = default_inferrer.is_int(value, allow_sign=True, allow_negative=True)
		assert is_int_allow_both_result == is_int_allow_both_expected

		is_int_disallow_negative_result = default_inferrer.is_int(value, allow_sign=False, allow_negative=False)
		assert is_int_disallow_negative_result == False

		if expected_int is None:
			with pytest.raises(ValueError):
				default_inferrer.to_int(value)
		else:
			result = default_inferrer.to_int(value)
			assert result == expected_int


	@staticmethod
	@pytest.mark.parametrize(
		('value', 'is_int_allow_scientific_expected', 'allow_scientific_expected'),
		# All test cases expect False when e disallowed
		[
			("0e0", True, 0),
			("0e1", True, 0),
			("1e0", True, 1),
			("1e1", True, 10),
			("1e2", True, 100),
			("2e3", True, 2000),
			("+3e2", True, 300),
			("-4e2", True, -400),
			("5e+2", True, 500),
			("60e2", True, 6000),
			("07e2", True, 700),
			("800e0", True, 800),
			("900e1", True, 9000),
			("1e9", True, 10 ** 9),
			("1_0e2", True, 1000),
			("1_0_0e1", True, 1000),
			("1e1_0", True, 10 ** 10),
			("1e-2", False, None),
			("100e-2", False, None),
			("100e-1", False, None),
			("1.e2", False, None),
			("_1e2", False, None),
			("1_e2", False, None),
			("1e_2", False, None),
			("1e2_", False, None),
			("1__0e2", False, None),
			("1e1__0", False, None),
			("1e", False, None),
			("e1", False, None),
			("e", False, None),
		]
	)
	def test_allow_scientific(default_inferrer: TypeParser, value: str, is_int_allow_scientific_expected: bool, allow_scientific_expected: int | None):
		is_int_allow_scientific_result = default_inferrer.is_int(value, allow_scientific=True)
		assert is_int_allow_scientific_result == is_int_allow_scientific_expected
		is_int_disallow_scientific_result = default_inferrer.is_int(value, allow_scientific=False)
		assert is_int_disallow_scientific_result == False

		if allow_scientific_expected is None:
			with pytest.raises(ValueError):
				default_inferrer.to_int(value, allow_scientific=True)
		else:
			allow_scientific_result = default_inferrer.to_int(value, allow_scientific=True)
			assert allow_scientific_result == allow_scientific_expected

		with pytest.raises(ValueError):
			default_inferrer.to_int(value, allow_scientific=False)


	@staticmethod
	@pytest.fixture
	def int_trim_inferrer(request: pytest.FixtureRequest) -> TypeParser:
		return TypeParser(trim=request.param)

	@staticmethod
	@pytest.mark.parametrize(
		('value', 'int_trim_inferrer', 'is_int_expected', 'expected_int'),
		[
			("1", True, True, 1),
			(" 1", True, True, 1),
			("1 ", True, True, 1),
			(" 1 ", True, True, 1),
			("1\n", True, True, 1),

			("1", False, True, 1),
			(" 1", False, False, None),
			("1 ", False, False, None),
			(" 1 ", False, False, None),
			("1\n", False, False, None),
		],
		indirect=['int_trim_inferrer']
	)
	def test_trim(
		value: str,
		int_trim_inferrer: TypeParser,
		is_int_expected: bool,
		expected_int: int | None,
	):
		is_int_result = int_trim_inferrer.is_int(value)
		assert is_int_result == is_int_expected

		if expected_int is None:
			with pytest.raises(ValueError):
				int_trim_inferrer.to_int(value)
		else:
			int_result = int_trim_inferrer.to_int(value)
			assert int_result == expected_int


class TestFloatDecimal:
	@staticmethod
	def check_float(result: float, expected: float) -> bool:
		if expected is math.nan:
			return result is math.nan
		else:
			return result == expected

	@staticmethod
	def check_decimal(result: Decimal, expected: Decimal) -> bool:
		if expected.is_nan():
			return result.is_nan()
		else:
			return result == expected


	@staticmethod
	@pytest.mark.parametrize(('value', 'is_float_expected', 'expected_int'), TestInt.int_test_cases)
	def test_default_int_as_float(default_inferrer: TypeParser, value: str, is_float_expected: bool, expected_int: int):
		is_float_result = default_inferrer.is_float(value)
		assert is_float_result == is_float_expected
		is_decimal_result = default_inferrer.is_decimal(value)
		assert is_decimal_result == is_float_expected

		if expected_int is None:
			with pytest.raises(ValueError):
				default_inferrer.to_float(value)
			with pytest.raises(ValueError):
				default_inferrer.to_decimal(value)
		else:
			float_result = default_inferrer.to_float(value)
			assert float_result == float(expected_int)
			decimal_result = default_inferrer.to_decimal(value)
			assert decimal_result == Decimal(expected_int)


	@staticmethod
	@pytest.mark.parametrize(
		('value', 'is_float_expected', 'expected_float', 'expected_decimal'),
		[
			("0.0", True, 0., Decimal(0)),
			("+0.0", True, 0., Decimal(0)),
			("-0.0", True, 0., Decimal(0)),
			("−0.0", True, 0., Decimal(0)),
			("0.", True, 0., Decimal(0)),
			("+0.", True, 0., Decimal(0)),
			("-0.", True, 0., Decimal(0)),
			("−0.", True, 0., Decimal(0)),
			(".0", True, 0., Decimal(0)),
			("+.0", True, 0., Decimal(0)),
			("-.0", True, 0., Decimal(0)),
			("−.0", True, 0., Decimal(0)),
			("1.0", True, 1., Decimal(1)),
			("2.", True, 2., Decimal(2)),
			("0.3", True, 0.3, Decimal(3) / Decimal(10)),
			(".4", True, 0.4, Decimal(4) / Decimal(10)),
			("0.05", True, 0.05, Decimal(5) / Decimal(100)),
			(".06", True, 0.06, Decimal(6) / Decimal(100)),
			("70.07", True, 70.07, Decimal(70) + Decimal(7) / Decimal(100)),
			("+8.8", True, 8.8, Decimal(8) + Decimal(8) / Decimal(10)),
			("-9.9", True, -9.9, Decimal(-9) - Decimal(9) / Decimal(10)),
			("−10.1", True, -10.1, Decimal(-10) - Decimal(1) / Decimal(10)),
			("-011.1", True, -11.1, Decimal(-11) - Decimal(1) / Decimal(10)),
			("+012.1", True, 12.1, Decimal(12) + Decimal(1) / Decimal(10)),
			("1_3.1", True, 13.1, Decimal(13) + Decimal(1) / Decimal(10)),
			("1_4.1_4", True, 14.14, Decimal(14) + Decimal(14) / Decimal(100)),
			("1000_0_00.0_0_0_001", True, 1e6 + 1e-6, Decimal(10) ** Decimal(6) + Decimal(10) ** Decimal(-6)),
			("a", False, None, None),
			("1a", False, None, None),
			("2.0b", False, None, None),
			("3.c", False, None, None),
			(".4d", False, None, None),
			("e5", False, None, None),
			("f6.0", False, None, None),
			("g7.", False, None, None),
			("h.8", False, None, None),
			("", False, None, None),
			("1__1.1", False, None, None),
			("_1.1", False, None, None),
			("1_.1", False, None, None),
			("_1_.1", False, None, None),
			("1._1", False, None, None),
			("1.1_", False, None, None),
			("1._1_", False, None, None),
			("1.1__1", False, None, None),
			("inf", False, None, None),
			("-inf", False, None, None),
			("nan", False, None, None),
			("", False, None, None),
		]
	)
	def test_default(default_inferrer: TypeParser, value: str, is_float_expected: bool, expected_float: float | None, expected_decimal: Decimal | None):
		is_float_result = default_inferrer.is_float(value)
		assert is_float_result == is_float_expected
		is_decimal_result = default_inferrer.is_decimal(value)
		assert is_decimal_result == is_float_expected

		if expected_float is None:
			with pytest.raises(ValueError):
				default_inferrer.to_float(value)
		else:
			float_result = default_inferrer.to_float(value)
			assert TestFloatDecimal.check_float(float_result, expected_float)

		if expected_decimal is None:
			with pytest.raises(ValueError):
				default_inferrer.to_decimal(value)
		else:
			decimal_result = default_inferrer.to_decimal(value)
			assert TestFloatDecimal.check_decimal(decimal_result, expected_decimal)


	@staticmethod
	@pytest.mark.parametrize(
		('value', 'is_float_expected', 'expected_float', 'expected_decimal'),
		# All test cases expect False when e disallowed
		[
			("2.3e0", True, 2.3, Decimal(2) + Decimal(3) / Decimal(10)),
			("+2.3e0", True, 2.3, Decimal(2) + Decimal(3) / Decimal(10)),
			("-2.3e0", True, -2.3, Decimal(-2) - Decimal(3) / Decimal(10)),
			("2.3e1", True, 23., Decimal(23)),
			("2.3e2", True, 230, Decimal(230)),
			("2.3e+2", True, 230, Decimal(230)),
			("2.3e-2", True, 0.023, Decimal(23) / Decimal(1000)),
			("02.3e2", True, 230, Decimal(230)),
			("2.3e02", True, 230, Decimal(230)),
			("2.3e1_0", True, 2.3e10, Decimal(23) * (Decimal(10) ** Decimal(9))),
			("_1.1e2", False, None, None),
			("1_.1e2", False, None, None),
			("_1_.1e2", False, None, None),
			("1._1e2", False, None, None),
			("1.1_e2", False, None, None),
			("1._1_e2", False, None, None),
			("1.1e_2", False, None, None),
			("1.1e2_", False, None, None),
			("1.1e_2_", False, None, None),
			("1.1e2__2", False, None, None),
			("1.1e2.2", False, None, None),
			("1.1e+2.2", False, None, None),
			("1.1e-2.2", False, None, None),
			("1.0e", False, None, None),
			("1.e", False, None, None),
			("1e", False, None, None),
			(".1e", False, None, None),
			("0.1e", False, None, None),
			("e1", False, None, None),
			("e1.", False, None, None),
			("e1.0", False, None, None),
			("e.1", False, None, None),
			("e0.1", False, None, None),
		]
	)
	def test_allow_scientific(default_inferrer: TypeParser, value: str, is_float_expected: bool, expected_float: float | None, expected_decimal: Decimal | None):
		is_float_result = default_inferrer.is_float(value, allow_scientific=True)
		assert is_float_result == is_float_expected
		is_decimal_result = default_inferrer.is_decimal(value, allow_scientific=True)
		assert is_decimal_result == is_float_expected

		if expected_float is None:
			with pytest.raises(ValueError):
				default_inferrer.to_float(value, allow_scientific=True)
		else:
			float_result = default_inferrer.to_float(value, allow_scientific=True)
			assert TestFloatDecimal.check_float(float_result, expected_float)
		with pytest.raises(ValueError):
			default_inferrer.to_float(value, allow_scientific=False)

		if expected_decimal is None:
			with pytest.raises(ValueError):
				default_inferrer.to_decimal(value, allow_scientific=True)
		else:
			decimal_result = default_inferrer.to_decimal(value, allow_scientific=True)
			assert TestFloatDecimal.check_decimal(decimal_result, expected_decimal)
		with pytest.raises(ValueError):
			default_inferrer.to_decimal(value, allow_scientific=False)


	@staticmethod
	@pytest.fixture
	def float_values_inferrer(request: pytest.FixtureRequest) -> TypeParser:
		return TypeParser(inf_values=request.param[0], nan_values=request.param[1], none_values=[])

	no_values = ([], [])
	empty_str_inf = ([""], [])
	float_values = ([" inf \n"], [" NAN \n"])

	@staticmethod
	@pytest.mark.parametrize(
		('value', 'float_values_inferrer', 'is_float_expected', 'expected_float', 'expected_decimal'),
		[
			("inf", float_values, True, math.inf, Decimal(math.inf)),
			("INF", float_values, True, math.inf, Decimal(math.inf)),
			("+iNf", float_values, True, math.inf, Decimal(math.inf)),
			("-inf", float_values, True, -1 * math.inf, -1 * Decimal(math.inf)),
			("−INF", float_values, True, -1 * math.inf, -1 * Decimal(math.inf)),
			("nan", float_values, True, math.nan, Decimal(math.nan)),
			("NAN", float_values, True, math.nan, Decimal(math.nan)),
			("+NaN", float_values, True, math.nan, Decimal(math.nan)),
			("-nan", float_values, True, math.nan, Decimal(math.nan)),
			("true", float_values, False, None, None),
			("1", float_values, True, 1, Decimal(1)),
			("", float_values, False, None, None),

			("inf", no_values, False, None, None),
			("nan", no_values, False, None, None),
			("", no_values, False, None, None),

			("", empty_str_inf, True, math.inf, Decimal(math.inf)),
			("+", empty_str_inf, True, math.inf, Decimal(math.inf)),
			("-", empty_str_inf, True, -1 * math.inf, -1 * Decimal(math.inf)),
			("−", empty_str_inf, True, -1 * math.inf, -1 * Decimal(math.inf)),
			("nan", empty_str_inf, False, None, None),
		],
		indirect=['float_values_inferrer']
	)
	def test_float_values(
		value: str,
		float_values_inferrer: TypeParser,
		is_float_expected: bool,
		expected_float: bool | None,
		expected_decimal: Decimal | None,
	):
		is_float_result = float_values_inferrer.is_float(value)
		assert is_float_result == is_float_expected
		is_decimal_result = float_values_inferrer.is_decimal(value)
		assert is_decimal_result == is_float_expected

		if expected_float is None:
			with pytest.raises(ValueError):
				float_values_inferrer.to_float(value)
		else:
			float_result = float_values_inferrer.to_float(value)
			assert TestFloatDecimal.check_float(float_result, expected_float)

		if expected_decimal is None:
			with pytest.raises(ValueError):
				float_values_inferrer.to_decimal(value)
		else:
			decimal_result = float_values_inferrer.to_decimal(value)
			assert TestFloatDecimal.check_decimal(decimal_result, expected_decimal)


	@staticmethod
	@pytest.mark.parametrize(
		('value', 'float_values_inferrer', 'is_float_expected', 'expected_float', 'expected_decimal'),
		# All test cases expect False when inf disallowed
		[
			("inf", float_values, True, math.inf, Decimal(math.inf)),
			("+inf", float_values, True, math.inf, Decimal(math.inf)),
			("-inf", float_values, True, -1 * math.inf, -1 * Decimal(math.inf)),
			("−inf", float_values, True, -1 * math.inf, -1 * Decimal(math.inf)),
			("inff", float_values, False, None, None),
		],
		indirect=['float_values_inferrer']
	)
	def test_allow_inf(float_values_inferrer: TypeParser, value: str, is_float_expected: bool, expected_float: float | None, expected_decimal: Decimal | None):
		is_float_result = float_values_inferrer.is_float(value, allow_inf=True)
		assert is_float_result == is_float_expected
		is_decimal_result = float_values_inferrer.is_decimal(value, allow_inf=True)
		assert is_decimal_result == is_float_expected

		if expected_float is None:
			with pytest.raises(ValueError):
				float_values_inferrer.to_float(value, allow_inf=True)
		else:
			float_result = float_values_inferrer.to_float(value, allow_inf=True)
			assert TestFloatDecimal.check_float(float_result, expected_float)
		with pytest.raises(ValueError):
			float_values_inferrer.to_float(value, allow_inf=False)

		if expected_decimal is None:
			with pytest.raises(ValueError):
				float_values_inferrer.to_decimal(value, allow_inf=True)
		else:
			decimal_result = float_values_inferrer.to_decimal(value, allow_inf=True)
			assert TestFloatDecimal.check_decimal(decimal_result, expected_decimal)
		with pytest.raises(ValueError):
			float_values_inferrer.to_decimal(value, allow_inf=False)


	@staticmethod
	@pytest.mark.parametrize(
		('value', 'float_values_inferrer', 'is_float_expected', 'expected_float', 'expected_decimal'),
		# All test cases expect False when inf disallowed
		[
			("nan", float_values, True, math.nan, Decimal(math.nan)),
			("+nan", float_values, True, math.nan, Decimal(math.nan)),
			("-nan", float_values, True, math.nan, Decimal(math.nan)),
			("−nan", float_values, True, math.nan, Decimal(math.nan)),
			("nann", float_values, False, None, None),
		],
		indirect=['float_values_inferrer']
	)
	def test_allow_nan(float_values_inferrer: TypeParser, value: str, is_float_expected: bool, expected_float: float | None, expected_decimal: Decimal | None):
		is_float_result = float_values_inferrer.is_float(value, allow_nan=True)
		assert is_float_result == is_float_expected
		is_decimal_result = float_values_inferrer.is_decimal(value, allow_nan=True)
		assert is_decimal_result == is_float_expected

		if expected_float is None:
			with pytest.raises(ValueError):
				float_values_inferrer.to_float(value, allow_nan=True)
		else:
			float_result = float_values_inferrer.to_float(value, allow_nan=True)
			assert TestFloatDecimal.check_float(float_result, expected_float)
		with pytest.raises(ValueError):
			float_values_inferrer.to_float(value, allow_nan=False)

		if expected_decimal is None:
			with pytest.raises(ValueError):
				float_values_inferrer.to_decimal(value, allow_nan=True)
		else:
			decimal_result = float_values_inferrer.to_decimal(value, allow_nan=True)
			assert TestFloatDecimal.check_decimal(decimal_result, expected_decimal)
		with pytest.raises(ValueError):
			float_values_inferrer.to_decimal(value, allow_nan=False)


	@staticmethod
	@pytest.fixture
	def float_case_sensitive_inferrer(request: pytest.FixtureRequest) -> TypeParser:
		return TypeParser(float_case_sensitive=request.param[0], inf_values=request.param[1], nan_values=request.param[2])

	@staticmethod
	@pytest.mark.parametrize(
		('value', 'float_case_sensitive_inferrer', 'is_float_expected', 'expected_float', 'expected_decimal'),
		[
			("inf", (False, *float_values), True, math.inf, Decimal(math.inf)),
			("INF", (False, *float_values), True, math.inf, Decimal(math.inf)),
			("iNf", (False, *float_values), True, math.inf, Decimal(math.inf)),
			("+inf", (False, *float_values), True, math.inf, Decimal(math.inf)),
			("+INF", (False, *float_values), True, math.inf, Decimal(math.inf)),
			("-inf", (False, *float_values), True, -1 * math.inf, -1 * Decimal(math.inf)),
			("−INF", (False, *float_values), True, -1 * math.inf, -1 * Decimal(math.inf)),
			("nan", (False, *float_values), True, math.nan, -1 * Decimal(math.nan)),
			("NAN", (False, *float_values), True, math.nan, -1 * Decimal(math.nan)),
			("NaN", (False, *float_values), True, math.nan, -1 * Decimal(math.nan)),
			("+nan", (False, *float_values), True, math.nan, -1 * Decimal(math.nan)),
			("+NAN", (False, *float_values), True, math.nan, -1 * Decimal(math.nan)),
			("-nan", (False, *float_values), True, math.nan, -1 * Decimal(math.nan)),
			("−NAN", (False, *float_values), True, math.nan, -1 * Decimal(math.nan)),

			("inf", (True, *float_values), True, math.inf, Decimal(math.inf)),
			("INF", (True, *float_values), False, None, None),
			("iNf", (True, *float_values), False, None, None),
			("+inf", (True, *float_values), True, math.inf, Decimal(math.inf)),
			("+INF", (True, *float_values), False, None, None),
			("-inf", (True, *float_values), True, -1 * math.inf, -1 * Decimal(math.inf)),
			("−INF", (True, *float_values), False, None, None),
			("nan", (True, *float_values), False, None, None),
			("NAN", (True, *float_values), True, math.nan, Decimal(math.nan)),
			("NaN", (True, *float_values), False, None, None),
			("+nan", (True, *float_values), False, None, None),
			("+NAN", (True, *float_values), True, math.nan, Decimal(math.nan)),
			("-nan", (True, *float_values), False, None, None),
			("−NAN", (True, *float_values), True, math.nan, Decimal(math.nan)),
		],
		indirect=['float_case_sensitive_inferrer']
	)
	def test_case_sensitive(
		value: str,
		float_case_sensitive_inferrer: TypeParser,
		is_float_expected: bool,
		expected_float: float | None,
		expected_decimal: Decimal | None
	):
		is_float_result = float_case_sensitive_inferrer.is_float(value)
		assert is_float_result == is_float_expected
		is_decimal_result = float_case_sensitive_inferrer.is_decimal(value)
		assert is_decimal_result == is_float_expected

		if expected_float is None:
			with pytest.raises(ValueError):
				float_case_sensitive_inferrer.to_float(value)
		else:
			float_result = float_case_sensitive_inferrer.to_float(value)
			assert TestFloatDecimal.check_float(float_result, expected_float)

		if expected_decimal is None:
			with pytest.raises(ValueError):
				float_case_sensitive_inferrer.to_decimal(value)
		else:
			decimal_result = float_case_sensitive_inferrer.to_decimal(value)
			assert TestFloatDecimal.check_decimal(decimal_result, expected_decimal)


	@staticmethod
	@pytest.fixture
	def float_trim_inferrer(request: pytest.FixtureRequest) -> TypeParser:
		return TypeParser(trim=request.param[0], inf_values=request.param[1], nan_values=request.param[2], none_values=[])

	@staticmethod
	@pytest.mark.parametrize(
		('value', 'float_trim_inferrer', 'is_float_expected', 'expected_float', 'expected_decimal'),
		[
			("inf", (True, *float_values), True, math.inf, Decimal(math.inf)),
			(" inf \n", (True, *float_values), True, math.inf, Decimal(math.inf)),
			("+inf", (True, *float_values), True, math.inf, Decimal(math.inf)),
			(" +inf \n", (True, *float_values), True, math.inf, Decimal(math.inf)),
			("+ inf \n", (True, *float_values), False, None, None),
			("-inf", (True, *float_values), True, -1 * math.inf, -1 * Decimal(math.inf)),
			(" −inf \n", (True, *float_values), True, -1 * math.inf, -1 * Decimal(math.inf)),
			("− inf \n", (True, *float_values), False, None, None),
			("nan", (True, *float_values), True, math.nan, Decimal(math.nan)),
			(" nan \n", (True, *float_values), True, math.nan, Decimal(math.nan)),
			("1.", (True, *float_values), True, 1., Decimal(1)),
			(" 1.", (True, *float_values), True, 1., Decimal(1)),
			("1. ", (True, *float_values), True, 1., Decimal(1)),
			(" 1. ", (True, *float_values), True, 1., Decimal(1)),
			("1.\n", (True, *float_values), True, 1., Decimal(1)),

			("inf", (False, *float_values), False, None, None),
			(" inf \n", (False, *float_values), True, math.inf, Decimal(math.inf)),
			("+inf", (False, *float_values), False, None, None),
			(" +inf \n", (False, *float_values), False, None, None),
			("+ inf \n", (False, *float_values), True, math.inf, Decimal(math.inf)),
			("-inf", (False, *float_values), False, None, None),
			(" −inf \n", (False, *float_values), False, None, None),
			("− inf \n", (False, *float_values), True, -1 * math.inf, -1 * Decimal(math.inf)),
			("nan", (False, *float_values), False, None, None),
			(" nan \n", (False, *float_values), True, math.nan, Decimal(math.nan)),
			("1.", (False, *float_values), True, 1., Decimal(1)),
			(" 1.", (False, *float_values), False, None, None),
			("1. ", (False, *float_values), False, None, None),
			(" 1. ", (False, *float_values), False, None, None),
			("1.\n", (False, *float_values), False, None, None),

			("", (True, *empty_str_inf), True, math.inf, Decimal(math.inf)),
			("+", (True, *empty_str_inf), True, math.inf, Decimal(math.inf)),
			("−", (True, *empty_str_inf), True, -1 * math.inf, -1 * Decimal(math.inf)),
			(" ", (True, *empty_str_inf), True, math.inf, Decimal(math.inf)),
			(" + \n", (True, *empty_str_inf), True, math.inf, Decimal(math.inf)),
			(" − \n", (True, *empty_str_inf), True, -1 * math.inf, -1 * Decimal(math.inf)),
			("", (False, *empty_str_inf), True, math.inf, Decimal(math.inf)),
			("+", (False, *empty_str_inf), True, math.inf, Decimal(math.inf)),
			("−", (False, *empty_str_inf), True, -1 * math.inf, -1 * Decimal(math.inf)),
			(" ", (False, *empty_str_inf), False, None, None),
			(" + \n", (False, *empty_str_inf), False, None, None),
			(" − \n", (False, *empty_str_inf), False, None, None),
		],
		indirect=['float_trim_inferrer']
	)
	def test_trim(
		value: str,
		float_trim_inferrer: TypeParser,
		is_float_expected: bool,
		expected_float: float | None,
		expected_decimal: Decimal | None,
	):
		is_float_result = float_trim_inferrer.is_float(value)
		assert is_float_result == is_float_expected
		is_decimal_result = float_trim_inferrer.is_decimal(value)
		assert is_decimal_result == is_float_expected

		if expected_float is None:
			with pytest.raises(ValueError):
				float_trim_inferrer.to_float(value)
		else:
			float_result = float_trim_inferrer.to_float(value)
			assert TestFloatDecimal.check_float(float_result, expected_float)

		if expected_decimal is None:
			with pytest.raises(ValueError):
				float_trim_inferrer.to_decimal(value)
		else:
			decimal_result = float_trim_inferrer.to_decimal(value)
			assert TestFloatDecimal.check_decimal(decimal_result, expected_decimal)


class TestInferType:
	@staticmethod
	@pytest.mark.parametrize(
		('value', 'expected'),
		[
			("true", bool),
			("false", bool),
			("TRUE", bool),
			("FALSE", bool),
			("0", int),
			("+0", int),
			("-0", int),
			("1", int),
			("+1", int),
			("-1", int),
			("20", int),
			("1e6", int),
			("0.0", Decimal),
			("+0.0", Decimal),
			("-0.0", Decimal),
			("0.", Decimal),
			("+0.", Decimal),
			("-0.", Decimal),
			(".0", Decimal),
			("+.0", Decimal),
			("-.0", Decimal),
			("1.0", Decimal),
			("+1.0", Decimal),
			("-1.0", Decimal),
			("1.", Decimal),
			(".1", Decimal),
			("1.1", Decimal),
			("1.23e0", Decimal),
			("1.23e-0", Decimal),
			("1.23e+0", Decimal),
			("1.23e1", Decimal),
			("1.23e-1", Decimal),
			("1.23e+1", Decimal),
			("1.23e6", Decimal),
			("a", str),
			("a1", str),
			("1a", str),
			("1a1", str),
			("a1a", str),
			("a,b,c", str),
			("1.0.0", str),
			("0+1", str),
			("1-1", str),
			("1e2.", str),
			("1e2e3", str),
			("a,", str),
			("a,b,c", str),
			("1,", str),
			("1,2,3", str),
			("a\n", str),
			("a\nb\nc\n", str),
			("", NoneType),

			("inf", str),
			("nan", str),
		]
	)
	def test_scalars_default(default_inferrer: TypeParser, value: str, expected: DatumType):
		result = default_inferrer.infer_type(value)
		assert result == expected


	@staticmethod
	@pytest.fixture
	def list_inferrer(request: pytest.FixtureRequest) -> TypeParser:
		return TypeParser(list_delimiter=request.param)

	@staticmethod
	@pytest.mark.parametrize(
		('value', 'list_inferrer', 'delimiter_expected', 'no_delimiter_expected'),
		[
			("a,a", ',', list[str], str),
			("a,b,c", ',', list[str], str),
			(",,a", ',', list[Nullable[str]], str),
			("a", ',', str, str),

			("true,false,true", ',', list[bool], str),
			("true:false:true", ':', list[bool], str),
			("truepfalseptrue", 'p', list[bool], str),
			(",,true", ',', list[Nullable[bool]], str),
			("true,false,true", 't', list[Nullable[str]], str),

			("0,1,2", ',', list[int], str),
			("0,01,-2,+3,4e5,-60,7_0", ',', list[int], str),
			("0.1,0.2,0.3", ',', list[Decimal], str),
			(",,0.4", ',', list[Nullable[Decimal]], str),
			("0.,.0,0.0,01.00,-0.2,+3.0,4.e+5,6e-7,-80.08,9_0e1_0", ',', list[Decimal], str),

			("false,1", ',', list[int], str),
			("false,1.", ',', list[Decimal], str),
			("false,,1.", ',', list[Nullable[Decimal]], str),
			("1,2.", ',', list[Decimal], str),
			("1,2.,a", ',', list[str], str),
			("1,2.,,a", ',', list[Nullable[str]], str),

			(",,,", ',', list[NoneType], str),
		],
		indirect=['list_inferrer']
	)
	def test_lists_default(
		default_inferrer: TypeParser,
		value: str,
		list_inferrer: TypeParser,
		delimiter_expected: DatumType,
		no_delimiter_expected: DatumType
	):
		result = list_inferrer.infer_type(value)
		assert result == delimiter_expected

		result = default_inferrer.infer_type(value)
		assert result == no_delimiter_expected


class TestInferTableTypes:
	@staticmethod
	@pytest.mark.parametrize(
		('rows', 'expected_reduce_types', 'expected'),
		[
			(
				[
					["1", "a", "1.0", "false"],
					["-2", "b", "-2.", "true"],
					["+3", "cc", "+0.3", ""],
					["false", "", "4", "false"],
				],
				[
					[int, int, int, bool],
					[str, str, str, NoneType],
					[Decimal, Decimal, Decimal, int],
					[bool, bool, NoneType, bool],
				],
				[int, str, Decimal, bool],
			),
			([], [], []),
			(
				[["1", "2", "3", "4"]],
				[[int], [int], [int], [int]],
				[int, int, int, int],
			),
			(
				[["1"], ["2"], ["3"], ["4"]],
				[[int, int, int, int]],
				[int],
			)
		]
	)
	def test_default(default_inferrer: TypeParser, rows: list[list[str]], expected_reduce_types: list[list[DatumType]], expected: list[DatumType]):
		with patch('parsetypes._parser.reduce_types', side_effect=expected) as mocked_reduce_types:
			result = default_inferrer.infer_table_types(rows)
			mocked_reduce_types.assert_has_calls([call(expected_call) for expected_call in expected_reduce_types])
			assert result == expected


	@staticmethod
	@pytest.mark.parametrize('rows', [
		[
			["1", "a", "1.0", "false"],
			["-2", "b", "-2.", "true"],
			["+3", "cc", "+0.3", ""],
			["false", "", "4", "false"],
		],
	])
	def test_infer_args(default_inferrer: TypeParser, rows: list[list[str]]):
		with patch.object(default_inferrer, 'infer_type') as mocked_infer_type:
			default_inferrer.infer_table_types(rows)

			expected_calls = []
			for row in rows:
				for value in row:
					expected_calls.append(
						call(value)
					)

			mocked_infer_type.assert_has_calls(expected_calls, any_order=True)


class TestConstructor:
	@staticmethod
	@pytest.mark.parametrize('list_delimiter', [',', '\n'])
	@pytest.mark.parametrize('none_values', [[], [""], ["none", "n"]])
	@pytest.mark.parametrize('true_values', [[], ["t", "tru"]])
	@pytest.mark.parametrize('false_values', [[], ["f", "fa"]])
	@pytest.mark.parametrize('inf_values', [['inf']])
	@pytest.mark.parametrize('nan_values', [['nan']])
	def test_args(
		list_delimiter: str,
		none_values: list[str],
		true_values: list[str],
		false_values: list[str],
		inf_values: list[str],
		nan_values: list[str],
	):
		inferrer = TypeParser(
			trim=False,
			list_delimiter=list_delimiter,
			none_values=none_values,
			none_case_sensitive=True,
			true_values=true_values,
			false_values=false_values,
			bool_case_sensitive=True,
			inf_values=inf_values,
			nan_values=nan_values,
			float_case_sensitive=True,
		)

		assert inferrer.trim == False
		assert inferrer.list_delimiter == list_delimiter
		assert set(inferrer.none_values) == set(none_values)
		assert inferrer.none_case_sensitive == True
		assert set(inferrer.true_values) == set(true_values)
		assert set(inferrer.false_values) == set(false_values)
		assert inferrer.bool_case_sensitive == True
		assert set(inferrer.inf_values) == set(inf_values)
		assert set(inferrer.nan_values) == set(nan_values)
		assert inferrer.float_case_sensitive == True


	@staticmethod
	@pytest.mark.parametrize('trim', [True, False])
	@pytest.mark.parametrize('none_values', [[], [""], ["  ", " \n"], [" none ", "n\n"]])
	@pytest.mark.parametrize('none_case_sensitive', [True, False])
	def test_none_values(
		trim: bool,
		none_values: list[str],
		none_case_sensitive: bool,
	):
		inferrer = TypeParser(
			trim=trim,
			none_values=none_values,
			none_case_sensitive=none_case_sensitive,
		)

		assert inferrer.trim == trim
		assert inferrer.none_case_sensitive == none_case_sensitive

		if trim and none_case_sensitive:
			assert {value.strip() for value in inferrer.none_values} == {expected.strip() for expected in none_values}
		if trim and not none_case_sensitive:
			assert {value.lower().strip() for value in inferrer.none_values} == {expected.lower().strip() for expected in none_values}
			assert {value.upper().strip() for value in inferrer.none_values} == {expected.upper().strip() for expected in none_values}
		if not trim and none_case_sensitive:
			assert set(inferrer.none_values) == set(none_values)
		if not trim and not none_case_sensitive:
			assert {value.lower() for value in inferrer.none_values} == {expected.lower() for expected in none_values}
			assert {value.upper() for value in inferrer.none_values} == {expected.upper() for expected in none_values}


	@staticmethod
	@pytest.mark.parametrize('trim', [True, False])
	@pytest.mark.parametrize('true_values', [[], ["t", "tru"], [" t ", "tru\n"], ["T", "tru"]])
	@pytest.mark.parametrize('false_values', [[], ["f", "fa"], [" f ", "fa\n"], ["F", "fa"]])
	@pytest.mark.parametrize('bool_case_sensitive', [True, False])
	def test_bool_values(
		trim: bool,
		true_values: list[str],
		false_values: list[str],
		bool_case_sensitive: bool,
	):
		inferrer = TypeParser(
			trim=trim,
			true_values=true_values,
			false_values=false_values,
			bool_case_sensitive=bool_case_sensitive,
		)

		assert inferrer.trim == trim
		assert inferrer.bool_case_sensitive == bool_case_sensitive

		if trim and bool_case_sensitive:
			assert {value.strip() for value in inferrer.true_values} == {expected.strip() for expected in true_values}
		if trim and not bool_case_sensitive:
			assert {value.lower().strip() for value in inferrer.true_values} == {expected.lower().strip() for expected in true_values}
			assert {value.upper().strip() for value in inferrer.true_values} == {expected.upper().strip() for expected in true_values}
		if not trim and bool_case_sensitive:
			assert set(inferrer.true_values) == set(true_values)
		if not trim and not bool_case_sensitive:
			assert {value.lower() for value in inferrer.true_values} == {expected.lower() for expected in true_values}
			assert {value.upper() for value in inferrer.true_values} == {expected.upper() for expected in true_values}

		if trim and bool_case_sensitive:
			assert {value.strip() for value in inferrer.false_values} == {expected.strip() for expected in false_values}
		if trim and not bool_case_sensitive:
			assert {value.lower().strip() for value in inferrer.false_values} == {expected.lower().strip() for expected in false_values}
			assert {value.upper().strip() for value in inferrer.false_values} == {expected.upper().strip() for expected in false_values}
		if not trim and bool_case_sensitive:
			assert set(inferrer.false_values) == set(false_values)
		if not trim and not bool_case_sensitive:
			assert {value.lower() for value in inferrer.false_values} == {expected.lower() for expected in false_values}
			assert {value.upper() for value in inferrer.false_values} == {expected.upper() for expected in false_values}


	@staticmethod
	@pytest.mark.parametrize('trim', [True, False])
	@pytest.mark.parametrize('inf_values', [[], ["inf", "i"], [" inf ", "i\n"], ["INF", "i"]])
	@pytest.mark.parametrize('nan_values', [[], ["nan", "n"], [" nan ", "n\n"], ["NaN", "n"]])
	@pytest.mark.parametrize('float_case_sensitive', [True, False])
	def test_float_values(
		trim: bool,
		inf_values: list[str],
		nan_values: list[str],
		float_case_sensitive: bool,
	):
		inferrer = TypeParser(
			trim=trim,
			inf_values=inf_values,
			nan_values=nan_values,
			float_case_sensitive=float_case_sensitive,
		)

		assert inferrer.trim == trim
		assert inferrer.float_case_sensitive == float_case_sensitive

		if trim and float_case_sensitive:
			assert {value.strip() for value in inferrer.inf_values} == {expected.strip() for expected in inf_values}
		if trim and not float_case_sensitive:
			assert {value.lower().strip() for value in inferrer.inf_values} == {expected.lower().strip() for expected in inf_values}
			assert {value.upper().strip() for value in inferrer.inf_values} == {expected.upper().strip() for expected in inf_values}
		if not trim and float_case_sensitive:
			assert set(inferrer.inf_values) == set(inf_values)
		if not trim and not float_case_sensitive:
			assert {value.lower() for value in inferrer.inf_values} == {expected.lower() for expected in inf_values}
			assert {value.upper() for value in inferrer.inf_values} == {expected.upper() for expected in inf_values}

		if trim and float_case_sensitive:
			assert {value.strip() for value in inferrer.nan_values} == {expected.strip() for expected in nan_values}
		if trim and not float_case_sensitive:
			assert {value.lower().strip() for value in inferrer.nan_values} == {expected.lower().strip() for expected in nan_values}
			assert {value.upper().strip() for value in inferrer.nan_values} == {expected.upper().strip() for expected in nan_values}
		if not trim and float_case_sensitive:
			assert set(inferrer.nan_values) == set(nan_values)
		if not trim and not float_case_sensitive:
			assert {value.lower() for value in inferrer.nan_values} == {expected.lower() for expected in nan_values}
			assert {value.upper() for value in inferrer.nan_values} == {expected.upper() for expected in nan_values}


	@staticmethod
	@pytest.mark.parametrize('none_case_sensitive', [True, False])
	@pytest.mark.parametrize('bool_case_sensitive', [True, False])
	@pytest.mark.parametrize('float_case_sensitive', [True, False])
	@pytest.mark.parametrize('case_sensitive', [True, False, None])
	def test_case_sensitive(none_case_sensitive: bool, bool_case_sensitive: bool, float_case_sensitive: bool, case_sensitive: bool | None):
		inferrer = TypeParser(
			none_case_sensitive=none_case_sensitive,
			bool_case_sensitive=bool_case_sensitive,
			float_case_sensitive=float_case_sensitive,
			case_sensitive=case_sensitive,
		)

		if case_sensitive is None:
			assert inferrer.none_case_sensitive == none_case_sensitive
			assert inferrer.bool_case_sensitive == bool_case_sensitive
			assert inferrer.float_case_sensitive == float_case_sensitive
		else:
			assert inferrer.none_case_sensitive == case_sensitive
			assert inferrer.bool_case_sensitive == case_sensitive
			assert inferrer.float_case_sensitive == case_sensitive


	@staticmethod
	@pytest.mark.parametrize('list_delimiter', ["", "1", "."])
	def test_invalid_list_delimiter(list_delimiter: str):
		with pytest.raises(ValueError):
			TypeParser(list_delimiter=list_delimiter)


	@staticmethod
	@pytest.mark.parametrize('none_values', [["true"], ["true", "false"], ["1"], ["2e6"], ["."]])
	def test_invalid_none_values(none_values: list[str]):
		with pytest.raises(ValueError):
			TypeParser(none_values=none_values)


	@staticmethod
	@pytest.mark.parametrize('bool_values', [[""], ["e"], ["1"], ["2e6"], ["."]])
	def test_invalid_bool_values(bool_values: list[str]):
		with pytest.raises(ValueError):
			TypeParser(true_values=bool_values)
		with pytest.raises(ValueError):
			TypeParser(false_values=bool_values)


	@staticmethod
	@pytest.mark.parametrize('float_values', [[""], ["true"], ["e"], ["1"], ["2e6"], ["."]])
	def test_invalid_float_values(float_values: list[str]):
		with pytest.raises(ValueError):
			TypeParser(inf_values=float_values)
		with pytest.raises(ValueError):
			TypeParser(nan_values=float_values)