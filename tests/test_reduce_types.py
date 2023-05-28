from decimal import Decimal

import pytest

from parsetypes import reduce_types, AnyValueType, Nullable

from parsetypes._compat import NoneType


@pytest.mark.parametrize(
	('types', 'expected'),
	[
		([bool], bool),
		([int], int),
		([float], float),
		([Decimal], Decimal),
		([str], str),

		([bool, bool, bool], bool),
		([int, int, int], int),
		([Decimal, Decimal, Decimal], Decimal),
		([float, float, float], float),
		([str, str, str], str),

		([bool, int], int),
		([int, Decimal], Decimal),
		([Decimal, float], float),
		([int, Decimal, float], float),
		([bool, str], str),
		([int, str], str),
		([Decimal, str], str),
		([float, str], str),
		([bool, int, float, Decimal, str], str),

		([], str),
	]
)
def test_reduce_scalar_types(types: list[AnyValueType], expected: AnyValueType):
	result = reduce_types(types)
	assert result == expected


@pytest.mark.parametrize(
	('types', 'expected'),
	[
		([list[bool], list[bool]], list[bool]),
		([list[int], list[int]], list[int]),
		([list[float], list[float]], list[float]),
		([list[Decimal], list[Decimal]], list[Decimal]),
		([list[str], list[str]], list[str]),

		([list[bool], list[int]], list[int]),
		([list[int], list[Decimal]], list[Decimal]),
		([list[Decimal], list[float]], list[float]),
		([list[int], list[Decimal], list[float]], list[float]),
		([list[bool], list[int], list[Decimal], list[float]], list[float]),
		([list[bool], list[int], list[Decimal], list[float], list[str]], list[str]),

		([list[bool], bool], list[bool]),
		([list[int], int], list[int]),
		([list[float], float], list[float]),
		([list[Decimal], Decimal], list[Decimal]),
		([list[str], str], list[str]),

		([list[bool], int], list[int]),
		([list[int], Decimal], list[Decimal]),
		([list[Decimal], float], list[float]),
		([list[int], float, Decimal], list[float]),
		([list[int], str], list[str]),

		#([list[list[bool]], list[list[bool]]], list[list[bool]]),
		#([list[list[int]], list[list[int]]], list[list[int]]),
		#([list[list[Decimal]], list[list[Decimal]]], list[list[Decimal]]),
		#([list[list[float]], list[list[float]]], list[list[float]]),
		#([list[list[str]], list[list[str]]], list[list[str]]),

		#([list[list[bool]], list[list[int]]], list[list[int]]),
		#([list[list[int]], list[list[Decimal]]], list[list[Decimal]]),
		#([list[list[Decimal]], list[list[float]]], list[list[float]]),
		#([list[list[float]], list[list[str]]], list[list[str]]),

		#([list[list[bool]], list[int]], list[list[int]]),
		#([list[list[int]], list[Decimal]], list[list[Decimal]]),
		#([list[list[Decimal]], list[float]], list[list[float]]),
		#([list[list[float]], list[str]], list[list[str]]),
	]
)
def test_reduce_list_types(types: list[AnyValueType], expected: AnyValueType):
	result = reduce_types(types)
	assert result == expected


@pytest.mark.parametrize(
	('types', 'expected'),
	[
		([Nullable[bool], Nullable[bool]], Nullable[bool]),
		([Nullable[int], Nullable[int]], Nullable[int]),
		([Nullable[float], Nullable[float]], Nullable[float]),
		([Nullable[Decimal], Nullable[Decimal]], Nullable[Decimal]),
		([Nullable[str], Nullable[str]], Nullable[str]),

		([Nullable[bool], Nullable[int]], Nullable[int]),
		([Nullable[int], Nullable[Decimal]], Nullable[Decimal]),
		([Nullable[Decimal], Nullable[float]], Nullable[float]),
		([Nullable[int], Nullable[Decimal], Nullable[float]], Nullable[float]),
		([Nullable[bool], Nullable[int], Nullable[Decimal], Nullable[float]], Nullable[float]),
		([Nullable[bool], Nullable[int], Nullable[Decimal], Nullable[float], Nullable[str]], Nullable[str]),

		([Nullable[bool], bool], Nullable[bool]),
		([Nullable[int], int], Nullable[int]),
		([Nullable[float], float], Nullable[float]),
		([Nullable[Decimal], Decimal], Nullable[Decimal]),
		([Nullable[str], str], Nullable[str]),

		([bool, Nullable[bool]], Nullable[bool]),
		([int, Nullable[int]], Nullable[int]),
		([float, Nullable[float]], Nullable[float]),
		([Decimal, Nullable[Decimal]], Nullable[Decimal]),
		([str, Nullable[str]], Nullable[str]),

		([Nullable[bool], int], Nullable[int]),
		([Nullable[int], Decimal], Nullable[Decimal]),
		([Nullable[Decimal], float], Nullable[float]),
		([Nullable[int], float, Decimal], Nullable[float]),
		([Nullable[int], str], Nullable[str]),

		([bool, Nullable[int]], Nullable[int]),
		([int, Nullable[Decimal]], Nullable[Decimal]),
		([Decimal, Nullable[float]], Nullable[float]),
		([int, Nullable[float], Decimal], Nullable[float]),
		([int, Nullable[str]], Nullable[str]),
	]
)
def test_reduce_nullable_types(types: list[AnyValueType], expected: AnyValueType):
	result = reduce_types(types)
	assert result == expected


@pytest.mark.parametrize(
	('types', 'expected'),
	[
		([Nullable[bool], list[bool]], list[bool]),
		([Nullable[int], list[int]], list[int]),
		([Nullable[float], list[float]], list[float]),
		([Nullable[Decimal], list[Decimal]], list[Decimal]),
		([Nullable[str], list[str]], list[str]),

		([list[bool], Nullable[int]], list[int]),
		([list[int], Nullable[Decimal]], list[Decimal]),
		([list[Decimal], Nullable[float]], list[float]),
		([list[int], Nullable[Decimal], Nullable[float]], list[float]),
		([list[bool], Nullable[int], Nullable[Decimal], Nullable[float]], list[float]),
		([list[bool], Nullable[int], Nullable[Decimal], Nullable[float], Nullable[str]], list[str]),
	]
)
def test_reduce_between_container_types(types: list[AnyValueType], expected: AnyValueType):
	result = reduce_types(types)
	assert result == expected


@pytest.mark.parametrize(
	('types', 'expected'),
	[
		([bool, NoneType], Nullable[bool]),
		([int, NoneType], Nullable[int]),
		([Decimal, NoneType], Nullable[Decimal]),
		([float, NoneType], Nullable[float]),
		([str, NoneType], Nullable[str]),

		([Nullable[bool], NoneType], Nullable[bool]),
		([Nullable[int], NoneType], Nullable[int]),
		([Nullable[Decimal], NoneType], Nullable[Decimal]),
		([Nullable[float], NoneType], Nullable[float]),
		([Nullable[str], NoneType], Nullable[str]),

		([bool, NoneType, int], Nullable[int]),
		([int, NoneType, Decimal], Nullable[Decimal]),
		([Decimal, NoneType, float], Nullable[float]),
		([float, NoneType, str], Nullable[str]),

		([list[bool], NoneType], list[bool]),
		([list[int], NoneType], list[int]),
		([list[Decimal], NoneType], list[Decimal]),
		([list[float], NoneType], list[float]),
		([list[str], NoneType], list[str]),

		([bool, NoneType, list[int]], list[int]),
		([int, NoneType, list[Decimal]], list[Decimal]),
		([Decimal, NoneType, list[float]], list[float]),
		([float, NoneType, list[str]], list[str]),
	]
)
def test_reduce_none_types(types: list[AnyValueType], expected: AnyValueType):
	result = reduce_types(types)
	assert result == expected


@pytest.mark.parametrize(
	('types', 'expected'),
	[
		([list[Nullable[bool]], list[Nullable[bool]]], list[Nullable[bool]]),
		([list[Nullable[int]], list[Nullable[int]]], list[Nullable[int]]),
		([list[Nullable[Decimal]], list[Nullable[Decimal]]], list[Nullable[Decimal]]),
		([list[Nullable[float]], list[Nullable[float]]], list[Nullable[float]]),
		([list[Nullable[str]], list[Nullable[str]]], list[Nullable[str]]),

		([list[Nullable[bool]], list[Nullable[int]]], list[Nullable[int]]),
		([list[Nullable[int]], list[Nullable[Decimal]]], list[Nullable[Decimal]]),
		([list[Nullable[Decimal]], list[Nullable[float]]], list[Nullable[float]]),
		([list[Nullable[float]], list[Nullable[str]]], list[Nullable[str]]),

		([list[Nullable[int]], Nullable[bool]], list[Nullable[int]]),
		([list[Nullable[Decimal]], Nullable[int]], list[Nullable[Decimal]]),
		([list[Nullable[float]], Nullable[Decimal]], list[Nullable[float]]),
		([list[Nullable[str]], Nullable[float]], list[Nullable[str]]),

		([list[Nullable[bool]], Nullable[int]], list[Nullable[int]]),
		([list[Nullable[int]], Nullable[Decimal]], list[Nullable[Decimal]]),
		([list[Nullable[Decimal]], Nullable[float]], list[Nullable[float]]),
		([list[Nullable[float]], Nullable[str]], list[Nullable[str]]),

		([list[Nullable[int]], list[bool]], list[Nullable[int]]),
		([list[Nullable[Decimal]], list[int]], list[Nullable[Decimal]]),
		([list[Nullable[float]], list[Decimal]], list[Nullable[float]]),
		([list[Nullable[str]], list[float]], list[Nullable[str]]),

		([list[Nullable[bool]], list[int]], list[Nullable[int]]),
		([list[Nullable[int]], list[Decimal]], list[Nullable[Decimal]]),
		([list[Nullable[Decimal]], list[float]], list[Nullable[float]]),
		([list[Nullable[float]], list[str]], list[Nullable[str]]),
	]
)
def test_reduce_list_nullable_types(types: list[AnyValueType], expected: AnyValueType):
	result = reduce_types(types)
	assert result == expected
