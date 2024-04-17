"""
These functions return ``cattrs.Converter`` instances.

Each ``Converter`` has an ``unstructure`` method,
which takes an object (usually a ``dict`` or YAML equivalent),
and returns a new one whose elements have been traversed and transformed.

The purpose is usually to prepare data for export into a given format,
with its particular type support.
"""

from __future__ import annotations

from datetime import date, datetime, time

try:
    from types import NoneType
except ImportError:
    NoneType = type(None)
from cattrs import Converter
from ruamel.yaml.comments import CommentedMap, CommentedSeq, TaggedScalar
from ruamel.yaml.scalarbool import ScalarBoolean
from ruamel.yaml.scalarfloat import ScalarFloat
from ruamel.yaml.scalarint import ScalarInt
from ruamel.yaml.scalarstring import ScalarString
from ruamel.yaml.timestamp import TimeStamp
from yamlpath.patches.timestamp import AnchoredDate


def _timestamp_to_datey(ts: TimeStamp) -> date | datetime:
    """
    Create a plain Python ``datetime.date`` or ``datetime.datetime``.

    Args:
        ts: a ``ruamel.yaml.timestamp.TimeStamp``,
            which may correspond to a date or time.

    Returns:
        A new ``datetime.date`` or ``datetime.datetime``,
            representing the value of ``ts``.
    """
    if isinstance(ts, AnchoredDate):
        return ts.date()
    return datetime.fromisoformat(ts.isoformat())


def mk_deep_converter() -> Converter:
    r"""
    Create a new recursively unstructuring ``cattrs.Converter``.

    It can traverse ``dict``\ s, ``list``\ s, and their ``ruamel.yaml`` equivalents.
    The other ``Converter``\ s here use this as a starting point,
    before adding more unstructuring hooks.

    Returns:
        A new, recursively unstructuring ``cattrs.Converter``.
    """
    c = Converter()

    c.register_unstructure_hook(list, lambda lst: [c.unstructure(e) for e in lst])
    c.register_unstructure_hook(
        dict, lambda d: {c.unstructure(k): c.unstructure(v) for k, v in d.items()}
    )

    c.register_unstructure_hook(CommentedSeq, lambda cs: [c.unstructure(e) for e in cs])
    c.register_unstructure_hook(
        CommentedMap, lambda cm: {c.unstructure(k): c.unstructure(v) for k, v in cm.items()}
    )

    return c


def mk_unyamlable_converter(time_marker: str) -> Converter:
    r"""
    Create a recursive ``Converter`` which replaces marked ``str``\ s with ``time`` instances.

    Args:
        time_marker: An arbitrary prefix (such as a UUID) which, when encountered,
            indicates the remainder of the containing ``str`` should be processed
            as ISO 8601 and the element replaced by a ``datetime.time`` instance.

    Returns:
        A ``Converter`` whose ``unstructure`` method replaces marked ``str``\ s with
            ``datetime.time`` instances.
    """
    c = mk_deep_converter()

    c.register_unstructure_hook(
        str,
        lambda s: (
            s if not s.startswith(time_marker) else time.fromisoformat(s.split(time_marker, 1)[1])
        ),
    )

    return c


def mk_stringy_converter() -> Converter:
    r"""
    Create a ``Converter`` which ``unstructure``\ s into plain ``str``/``list``/``dict`` objects.

    This might alternatively have been named ``mk_nestedtext_types_converter``.

    Returns:
        A ``Converter`` ready to ``unstructure`` nested data into only
            ``dict``/``list``/``str`` types.
    """
    c = mk_deep_converter()

    c.register_unstructure_hook(bool, str)
    c.register_unstructure_hook(int, str)
    c.register_unstructure_hook(float, str)
    c.register_unstructure_hook(NoneType, lambda _: '')

    c.register_unstructure_hook(ScalarString, str)
    c.register_unstructure_hook(ScalarBoolean, lambda sb: str(bool(sb)))
    c.register_unstructure_hook(ScalarInt, lambda si: str(int(si)))
    c.register_unstructure_hook(ScalarFloat, lambda sf: str(float(sf)))
    c.register_unstructure_hook(TaggedScalar, str)

    c.register_unstructure_hook(datetime, datetime.isoformat)
    c.register_unstructure_hook(date, date.isoformat)
    c.register_unstructure_hook(time, time.isoformat)

    c.register_unstructure_hook(AnchoredDate, lambda ad: _timestamp_to_datey(ad).isoformat())
    c.register_unstructure_hook(TimeStamp, TimeStamp.isoformat)

    return c


def mk_json_types_converter() -> Converter:
    r"""
    Create a ``Converter`` which ``unstructure``\ s into JSON-supported types.

    Returns:
        A ``Converter`` whose ``unstructure`` method results in nested objects of type
            ``str``/``int``/``float``/``bool``/``dict``/``list``/``None``
    """
    c = mk_deep_converter()

    c.register_unstructure_hook(ScalarString, str)
    c.register_unstructure_hook(ScalarBoolean, bool)
    c.register_unstructure_hook(ScalarInt, int)
    c.register_unstructure_hook(ScalarFloat, float)
    c.register_unstructure_hook(TaggedScalar, str)

    c.register_unstructure_hook(datetime, datetime.isoformat)
    c.register_unstructure_hook(date, date.isoformat)
    c.register_unstructure_hook(time, time.isoformat)

    c.register_unstructure_hook(AnchoredDate, lambda ad: _timestamp_to_datey(ad).isoformat())
    c.register_unstructure_hook(TimeStamp, TimeStamp.isoformat)

    return c


def mk_yaml_types_converter() -> Converter:
    r"""
    Create a ``Converter`` which ``unstructure``\ s into YAML-supported types.

    Returns:
        A ``Converter`` whose ``unstructure`` method results in nested objects of type
            ``str``/``int``/``float``/``bool``/``dict``/``list``/``None``/``datetime``/``date``
    """
    c = mk_deep_converter()

    c.register_unstructure_hook(ScalarString, str)
    c.register_unstructure_hook(ScalarBoolean, bool)
    c.register_unstructure_hook(ScalarInt, int)
    c.register_unstructure_hook(ScalarFloat, float)
    c.register_unstructure_hook(TaggedScalar, str)

    c.register_unstructure_hook(time, time.isoformat)

    c.register_unstructure_hook(TimeStamp, _timestamp_to_datey)

    return c


def mk_toml_types_converter() -> Converter:
    r"""
    Create a ``Converter`` which ``unstructure``\ s into TOML-supported types.

    Returns:
        A ``Converter`` whose ``unstructure`` method results in nested objects of type
            ``str``/``int``/``float``/``bool``/``dict``/``list``/``datetime``/``date``/``time``
    """
    c = mk_deep_converter()

    c.register_unstructure_hook(ScalarString, str)
    c.register_unstructure_hook(ScalarBoolean, bool)
    c.register_unstructure_hook(ScalarInt, int)
    c.register_unstructure_hook(ScalarFloat, float)
    c.register_unstructure_hook(TaggedScalar, str)

    c.register_unstructure_hook(TimeStamp, _timestamp_to_datey)

    return c
