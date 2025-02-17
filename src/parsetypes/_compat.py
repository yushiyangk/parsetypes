import sys
import types
import typing


# Required for versions < 3.10
Union = typing.Union


if sys.version_info >= (3, 10):
	NoneType = types.NoneType
	TypeAlias = typing.TypeAlias
else:
	NoneType = type(None)
	TypeAlias = typing.Any
