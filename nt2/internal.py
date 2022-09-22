import sys
from datetime import date, datetime, time
from json import dump as jdump, dumps as jdumps, load as jload
from types import NoneType, SimpleNamespace
from typing import Sequence

from cattrs import Converter as CAConverter
from nestedtext import dump as ntdump, load as ntload
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarbool import ScalarBoolean
from ruamel.yaml.scalarfloat import ScalarFloat
from ruamel.yaml.scalarint import ScalarInt
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
from ruamel.yaml.timestamp import TimeStamp
from yamlpath import Processor as YPProcessor
from yamlpath.common import Parsers as YPParsers
# from yamlpath.enums import YAMLValueFormats
from yamlpath.wrappers import ConsolePrinter as YPConsolePrinter

try:
    from rich.traceback import install as rich_tb_install
except ImportError:
    pass
else:
    rich_tb_install()

try:
    from rtoml import dump as tdump, load as tload
except ImportError:
    TOML_SUPPORT = False
else:
    TOML_SUPPORT = True
    from pathlib import Path

YAML_EDITOR = YPParsers.get_yaml_editor()
YAML_EDITOR.indent(mapping=2, sequence=4, offset=2)
ydump = YAML_EDITOR.dump
yload = YAML_EDITOR.load


def str_to_bool(value: str) -> bool:
    if value.lower() in ('true', 'yes', 'y', 'on', '1'):
        return True
    if value.lower() in ('false', 'no', 'n', 'off', '0'):
        return False
    raise ValueError


def mk_deep_converter() -> CAConverter:
    c = CAConverter()

    c.register_unstructure_hook(list, lambda lst: [c.unstructure(e) for e in lst])
    c.register_unstructure_hook(
        dict, lambda d: {c.unstructure(k): c.unstructure(v) for k, v in d.items()}
    )

    c.register_unstructure_hook(CommentedSeq, lambda cs: [c.unstructure(e) for e in cs])
    c.register_unstructure_hook(
        CommentedMap,
        lambda cm: {c.unstructure(k): c.unstructure(v) for k, v in cm.items()},
    )

    return c


def mk_stringy_converter():  # mk_nt_types_converter
    c = mk_deep_converter()

    c.register_unstructure_hook(bool, str)
    c.register_unstructure_hook(int, str)
    c.register_unstructure_hook(float, str)
    c.register_unstructure_hook(NoneType, lambda _: '')

    c.register_unstructure_hook(DoubleQuotedScalarString, str)
    c.register_unstructure_hook(ScalarBoolean, lambda sb: str(bool(sb)))
    c.register_unstructure_hook(ScalarInt, lambda si: str(int(si)))
    c.register_unstructure_hook(ScalarFloat, lambda sf: str(float(sf)))

    c.register_unstructure_hook(datetime, datetime.isoformat)
    c.register_unstructure_hook(date, date.isoformat)
    c.register_unstructure_hook(time, time.isoformat)

    c.register_unstructure_hook(TimeStamp, TimeStamp.isoformat)

    return c


def mk_json_types_converter():
    c = mk_deep_converter()

    c.register_unstructure_hook(DoubleQuotedScalarString, str)
    c.register_unstructure_hook(ScalarBoolean, bool)
    c.register_unstructure_hook(ScalarInt, int)
    c.register_unstructure_hook(ScalarFloat, float)

    c.register_unstructure_hook(datetime, datetime.isoformat)
    c.register_unstructure_hook(date, date.isoformat)
    c.register_unstructure_hook(time, time.isoformat)

    c.register_unstructure_hook(TimeStamp, TimeStamp.isoformat)

    return c


def mk_yaml_types_converter():
    c = mk_deep_converter()

    c.register_unstructure_hook(DoubleQuotedScalarString, str)
    c.register_unstructure_hook(ScalarBoolean, bool)
    c.register_unstructure_hook(ScalarInt, int)
    c.register_unstructure_hook(ScalarFloat, float)

    # c.register_unstructure_hook(datetime, datetime...)
    # c.register_unstructure_hook(date, date...)
    # c.register_unstructure_hook(time, time...)
    # c.register_unstructure_hook(TimeStamp, TimeStamp...)

    return c


# TODO: def mk_toml_types_converter():


def cast_stringy_data(
    data: dict | list,
    bool_paths: Sequence[str] = (),
    null_paths: Sequence[str] = (),
    num_paths: Sequence[str] = (),
    date_paths: Sequence[str] = (),
    converter: None | CAConverter = None,
) -> dict | list:
    if not any((bool_paths, null_paths, num_paths, date_paths)):
        return dict(data) if isinstance(data, dict) else list(data)

    log = YPConsolePrinter(SimpleNamespace(quiet=True, verbose=False, debug=False))
    doc, success = YPParsers.get_yaml_data(YAML_EDITOR, log, jdumps(data), literal=True)
    if not success:
        raise ValueError
    surgeon = YPProcessor(log, doc)

    for query_path in null_paths:
        for match in surgeon.get_nodes(query_path):
            if not match.node:
                surgeon.set_value(match.path, None)

    for query_path in bool_paths:
        for match in surgeon.get_nodes(query_path):
            if match.node is not None:
                surgeon.set_value(match.path, str_to_bool(match.node))
    for query_path in num_paths:
        for match in surgeon.get_nodes(query_path):
            if match.node is not None:
                num = float(match.node)
                try:
                    inum = int(num)
                except ValueError:
                    surgeon.set_value(match.path, num)
                else:
                    surgeon.set_value(match.path, inum if num == inum else num)

    # TODO: We can't yet manage setting a date/datetime object with surgeon.set_value...
    for query_path in date_paths:
        for match in surgeon.get_nodes(query_path):
            if match.node is not None:
                try:
                    timey_wimey = date.fromisoformat(match.node)
                except ValueError:
                    timey_wimey = TimeStamp.fromisoformat(match.node)
                surgeon.set_value(match.path, timey_wimey)
                # surgeon.set_value(match.path, timey_wimey, value_format=YAMLValueFormats.BARE)

    return (converter or mk_json_types_converter()).unstructure(doc)


def dump_json_to_nestedtext(*input_files):
    # We may need to use a converter.unstructure here; We'll see.
    if not input_files:
        typed_data = jload(sys.stdin)
        ntdump(typed_data, sys.stdout, indent=2)
    else:
        for f in input_files:
            with open(f) as ifile:
                typed_data = jload(ifile)
                ntdump(typed_data, sys.stdout, indent=2)


def dump_yaml_to_nestedtext(*input_files):
    converter = mk_stringy_converter()
    if not input_files:
        data = yload(sys.stdin)
        data = converter.unstructure(data)
        ntdump(data, sys.stdout, indent=2)
    else:
        for f in input_files:
            with open(f) as ifile:
                data = yload(ifile)
                data = converter.unstructure(data)
                ntdump(data, sys.stdout, indent=2)


def require_toml_support():
    if not TOML_SUPPORT:
        raise ImportError("TOML support for nt2 is not installed. Try reinstalling as 'nt2[toml]'")


def dump_toml_to_nestedtext(*input_files):
    require_toml_support()
    converter = mk_stringy_converter()
    if not input_files:
        data = tload(sys.stdin)
        data = converter.unstructure(data)
        ntdump(data, sys.stdout, indent=2)
    else:
        for f in input_files:
            data = tload(Path(f))
            data = converter.unstructure(data)
            ntdump(data, sys.stdout, indent=2)


def dump_nestedtext_to_yaml(
    *input_files, bool_paths=(), null_paths=(), num_paths=(), date_paths=()
):
    for src in input_files or (sys.stdin,):
        data = ntload(src)
        data = cast_stringy_data(
            data,
            bool_paths=bool_paths,
            null_paths=null_paths,
            num_paths=num_paths,
            date_paths=date_paths,
            converter=mk_yaml_types_converter(),
        )
        ydump(data, sys.stdout)


def dump_nestedtext_to_toml(
    *input_files, bool_paths=(), null_paths=(), num_paths=(), date_paths=()
):
    require_toml_support()
    for src in input_files or (sys.stdin,):
        data = ntload(src)
        data = cast_stringy_data(
            data,
            bool_paths=bool_paths,
            null_paths=null_paths,
            num_paths=num_paths,
            date_paths=date_paths,
            converter=mk_yaml_types_converter(),
        )
        # TODO: do we need a toml types converter, or will the yaml one do?
        # TODO: date support
        tdump(data, sys.stdout, pretty=True)


def dump_nestedtext_to_json(*input_files, bool_paths=(), null_paths=(), num_paths=()):
    for src in input_files or (sys.stdin,):
        data = ntload(src)
        data = cast_stringy_data(
            data,
            bool_paths=bool_paths,
            null_paths=null_paths,
            num_paths=num_paths,
            converter=mk_json_types_converter(),
        )
        jdump(data, sys.stdout, indent=2)
