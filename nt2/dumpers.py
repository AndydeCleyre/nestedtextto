from __future__ import annotations

import sys
from json import dump as jdump, loads as jloads
from json.decoder import JSONDecodeError

from nestedtext import dump as ntdump, load as ntload
from yamlpath.common import Parsers as YPParsers

from .casters import cast_stringy_data
from .converters import (
    mk_json_types_converter, mk_stringy_converter, mk_toml_types_converter, mk_yaml_types_converter
)

try:
    from tomli import load as tload, loads as tloads
    from tomli_w import dumps as tdumps
except ImportError:
    TOML_SUPPORT = False
else:
    TOML_SUPPORT = True

YAML_EDITOR = YPParsers.get_yaml_editor()
YAML_EDITOR.indent(mapping=2, sequence=4, offset=2)
ydump = YAML_EDITOR.dump
yload = YAML_EDITOR.load


def dump_json_to_nestedtext(*input_files):
    # We may need to use a converter.unstructure here; We'll see.
    if not input_files:

        content = sys.stdin.read()
        try:
            typed_data = jloads(content)
        except JSONDecodeError:
            typed_data = [jloads(line) for line in content.splitlines()]

        ntdump(typed_data, sys.stdout, indent=2)
    else:
        for f in input_files:

            content = f.read()
            try:
                typed_data = jloads(content)
            except JSONDecodeError:
                typed_data = [jloads(line) for line in content.splitlines()]

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
        data = tloads(sys.stdin.read())
        data = converter.unstructure(data)
        ntdump(data, sys.stdout, indent=2)
    else:
        for f in input_files:
            with open(f, 'rb') as ifile:
                data = tload(ifile)
            data = converter.unstructure(data)
            ntdump(data, sys.stdout, indent=2)


def dump_nestedtext_to_yaml(
    *input_files, bool_paths=(), null_paths=(), num_paths=(), date_paths=()
):
    for src in input_files or (sys.stdin,):
        data = ntload(src, 'any')
        data = cast_stringy_data(
            data,
            bool_paths=bool_paths,
            null_paths=null_paths,
            num_paths=num_paths,
            date_paths=date_paths,
            converter=mk_yaml_types_converter(),
        )
        ydump(data, sys.stdout)


def dump_nestedtext_to_toml(*input_files, bool_paths=(), num_paths=(), date_paths=()):
    require_toml_support()
    for src in input_files or (sys.stdin,):
        data = ntload(src, 'any')
        data = cast_stringy_data(
            data,
            bool_paths=bool_paths,
            num_paths=num_paths,
            date_paths=date_paths,
            converter=mk_toml_types_converter(),
        )
        if isinstance(data, list):
            data = {'TOML does not allow top-level arrays': data}
        print(tdumps(data, multiline_strings=True), end='')


def dump_nestedtext_to_json(*input_files, bool_paths=(), null_paths=(), num_paths=()):
    for src in input_files or (sys.stdin,):
        data = ntload(src, 'any')
        data = cast_stringy_data(
            data,
            bool_paths=bool_paths,
            null_paths=null_paths,
            num_paths=num_paths,
            converter=mk_json_types_converter(),
        )
        jdump(data, sys.stdout, indent=2)
