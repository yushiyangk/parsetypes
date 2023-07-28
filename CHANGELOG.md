## Changelog

This project follows [PEP 440](https://peps.python.org/pep-0440/) and [Semantic Versioning (SemVer)](https://semver.org/spec/v2.0.0.html). In addition to the guarantees specified by SemVer, for versions before 1.0, this project guarantees backwards compatibility of the API for patch version updates (0.<var>y</var>.<b><var>z</var></b>).

The recommended version specifier is <code>parsetypes ~= <var>x</var>.<var>y</var></code> for version 1.0 and later, and <code>parsetypes ~= <var>0</var>.<var>y</var>.<var>z</var></code> for versions prior to 1.0.

### 0.3.2

- Improved documentation

### 0.3.1

- Added the arguments `allow_negative` and `allow_sign` (both `True` by default) to <code><var>parser</var>.parse_int()</code>, for parity with <code><var>parser</var>.is_int()</code> which already had these arguments

### 0.3

- Made the previously public but undocumented instance variables of TypeParser that corresponded to the constructor arguments private instead
- Added public properties to TypeParser for accessing or modifying the same settings in a controlled manner

### 0.2.6

- Added `Nullable` to automatic imports via `from parsetypes import *` (previously only `TypeParser` and `reduce_types` were imported)

### 0.2.5

- Fixed documentation

### 0.2.4

- Added <code><var>parser</var>.convert()</code>

### 0.2.1, 0.2.2, 0.2.3

- Fixed documentation

### 0.2

- Added support for Python version 3.9; previously only 3.10 and 3.11 were supported

### 0.1.1

- Updated documentation

### 0.1

- Initial version
