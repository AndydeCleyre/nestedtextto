from __future__ import annotations

from datetime import date, datetime, time

try:
    from types import NoneType
except ImportError:
    NoneType = type(None)
from cattrs import Converter
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarbool import ScalarBoolean
from ruamel.yaml.scalarfloat import ScalarFloat
from ruamel.yaml.scalarint import ScalarInt
from ruamel.yaml.scalarstring import ScalarString
from ruamel.yaml.timestamp import TimeStamp
from yamlpath.patches.timestamp import AnchoredDate


def timestamp_to_datey(ts: TimeStamp) -> date | datetime:
    if isinstance(ts, AnchoredDate):
        return ts.date()
    return datetime.fromisoformat(ts.isoformat())


def mk_deep_converter() -> Converter:
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


def mk_marked_string_converter(time_marker: str) -> Converter:
    c = mk_deep_converter()

    c.register_unstructure_hook(
        str,
        lambda s: s
        if not s.startswith(time_marker)
        else time.fromisoformat(s.split(time_marker, 1)[1]),
    )

    return c


def mk_stringy_converter() -> Converter:  # mk_nt_types_converter
    c = mk_deep_converter()

    c.register_unstructure_hook(bool, str)
    c.register_unstructure_hook(int, str)
    c.register_unstructure_hook(float, str)
    c.register_unstructure_hook(NoneType, lambda _: '')

    c.register_unstructure_hook(ScalarString, str)
    c.register_unstructure_hook(ScalarBoolean, lambda sb: str(bool(sb)))
    c.register_unstructure_hook(ScalarInt, lambda si: str(int(si)))
    c.register_unstructure_hook(ScalarFloat, lambda sf: str(float(sf)))

    c.register_unstructure_hook(datetime, datetime.isoformat)
    c.register_unstructure_hook(date, date.isoformat)
    c.register_unstructure_hook(time, time.isoformat)

    c.register_unstructure_hook(AnchoredDate, lambda ad: timestamp_to_datey(ad).isoformat())
    c.register_unstructure_hook(TimeStamp, TimeStamp.isoformat)

    return c


def mk_json_types_converter() -> Converter:
    c = mk_deep_converter()

    c.register_unstructure_hook(ScalarString, str)
    c.register_unstructure_hook(ScalarBoolean, bool)
    c.register_unstructure_hook(ScalarInt, int)
    c.register_unstructure_hook(ScalarFloat, float)

    c.register_unstructure_hook(datetime, datetime.isoformat)
    c.register_unstructure_hook(date, date.isoformat)
    c.register_unstructure_hook(time, time.isoformat)

    c.register_unstructure_hook(AnchoredDate, lambda ad: timestamp_to_datey(ad).isoformat())
    c.register_unstructure_hook(TimeStamp, TimeStamp.isoformat)

    return c


def mk_yaml_types_converter() -> Converter:
    c = mk_deep_converter()

    c.register_unstructure_hook(ScalarString, str)
    c.register_unstructure_hook(ScalarBoolean, bool)
    c.register_unstructure_hook(ScalarInt, int)
    c.register_unstructure_hook(ScalarFloat, float)

    c.register_unstructure_hook(time, time.isoformat)

    c.register_unstructure_hook(TimeStamp, timestamp_to_datey)

    return c


def mk_toml_types_converter() -> Converter:
    c = mk_deep_converter()

    c.register_unstructure_hook(ScalarString, str)
    c.register_unstructure_hook(ScalarBoolean, bool)
    c.register_unstructure_hook(ScalarInt, int)
    c.register_unstructure_hook(ScalarFloat, float)

    c.register_unstructure_hook(TimeStamp, timestamp_to_datey)

    return c
