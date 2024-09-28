"""
Register Hypothesis strategies for Pydantic custom types.

This enables fully-automatic generation of test data for most Pydantic classes.

Note that this module has *no* runtime impact on Pydantic itself; instead it
is registered as a setuptools entry point and Hypothesis will import it if
Pydantic is installed.  See also:

https://hypothesis.readthedocs.io/en/latest/strategies.html#registering-strategies-via-setuptools-entry-points
https://hypothesis.readthedocs.io/en/latest/data.html#hypothesis.strategies.register_type_strategy
https://hypothesis.readthedocs.io/en/latest/strategies.html#interaction-with-pytest-cov
https://docs.pydantic.dev/usage/types/#pydantic-types

Note that because our motivation is to *improve user experience*, the strategies
are always sound (never generate invalid data) but sacrifice completeness for
maintainability (ie may be unable to generate some tricky but valid data).

Finally, this module makes liberal use of `# type: ignore[<code>]` pragmas.
This is because Hypothesis annotates `register_type_strategy()` with
`(T, SearchStrategy[T])`, but in most cases we register e.g. `ConstrainedInt`
to generate instances of the builtin `int` type which match the constraints.
"""
import contextlib
import datetime
import ipaddress
import json
import math
from fractions import Fraction
from typing import Callable, Dict, Type, Union, cast, overload
import hypothesis.strategies as st
import pydantic
import pydantic.color
import pydantic.types
from pydantic.v1.utils import lenient_issubclass
try:
    import email_validator
except ImportError:
    pass
else:
    st.register_type_strategy(pydantic.EmailStr, st.emails().filter(is_valid_email))
    st.register_type_strategy(pydantic.NameEmail, st.builds('{} <{}>'.format, st.from_regex('[A-Za-z0-9_]+( [A-Za-z0-9_]+){0,5}', fullmatch=True), st.emails().filter(is_valid_email)))
st.register_type_strategy(pydantic.PyObject, st.sampled_from([cast(pydantic.PyObject, f'math.{name}') for name in sorted(vars(math)) if not name.startswith('_')]))
_color_regexes = '|'.join((pydantic.color.r_hex_short, pydantic.color.r_hex_long, pydantic.color.r_rgb, pydantic.color.r_rgba, pydantic.color.r_hsl, pydantic.color.r_hsla)).replace(pydantic.color._r_sl, '(?:(\\d\\d?(?:\\.\\d+)?|100(?:\\.0+)?)%)').replace(pydantic.color._r_alpha, '(?:(0(?:\\.\\d+)?|1(?:\\.0+)?|\\.\\d+|\\d{1,2}%))').replace(pydantic.color._r_255, '(?:((?:\\d|\\d\\d|[01]\\d\\d|2[0-4]\\d|25[0-4])(?:\\.\\d+)?|255(?:\\.0+)?))')
st.register_type_strategy(pydantic.color.Color, st.one_of(st.sampled_from(sorted(pydantic.color.COLORS_BY_NAME)), st.tuples(st.integers(0, 255), st.integers(0, 255), st.integers(0, 255), st.none() | st.floats(0, 1) | st.floats(0, 100).map('{}%'.format)), st.from_regex(_color_regexes, fullmatch=True)))
card_patterns = ('4[0-9]{14}', '5[12345][0-9]{13}', '3[47][0-9]{12}', '[0-26-9][0-9]{10,17}')
st.register_type_strategy(pydantic.PaymentCardNumber, st.from_regex('|'.join(card_patterns), fullmatch=True).map(add_luhn_digit))
st.register_type_strategy(pydantic.UUID1, st.uuids(version=1))
st.register_type_strategy(pydantic.UUID3, st.uuids(version=3))
st.register_type_strategy(pydantic.UUID4, st.uuids(version=4))
st.register_type_strategy(pydantic.UUID5, st.uuids(version=5))
st.register_type_strategy(pydantic.SecretBytes, st.binary().map(pydantic.SecretBytes))
st.register_type_strategy(pydantic.SecretStr, st.text().map(pydantic.SecretStr))
st.register_type_strategy(pydantic.IPvAnyAddress, st.ip_addresses())
st.register_type_strategy(pydantic.IPvAnyInterface, st.from_type(ipaddress.IPv4Interface) | st.from_type(ipaddress.IPv6Interface))
st.register_type_strategy(pydantic.IPvAnyNetwork, st.from_type(ipaddress.IPv4Network) | st.from_type(ipaddress.IPv6Network))
st.register_type_strategy(pydantic.StrictBool, st.booleans())
st.register_type_strategy(pydantic.StrictStr, st.text())
st.register_type_strategy(pydantic.FutureDate, st.dates(min_value=datetime.date.today() + datetime.timedelta(days=1)))
st.register_type_strategy(pydantic.PastDate, st.dates(max_value=datetime.date.today() - datetime.timedelta(days=1)))
RESOLVERS: Dict[type, Callable[[type], st.SearchStrategy]] = {}
for typ in list(pydantic.types._DEFINED_TYPES):
    _registered(typ)
pydantic.types._registered = _registered
st.register_type_strategy(pydantic.Json, resolve_json)