"""Main functions to be called by the UI Application classes, after CLI option parsing."""
from __future__ import annotations

import sys
from json import dump as _jdump, dumps as _jdumps, loads as _jloads
from json.decoder import JSONDecodeError

from nestedtext import dump as _ntdump, dumps as _ntdumps, load as ntload
from rich.console import Console as RichConsole
from rich.syntax import Syntax as RichSyntax
from yamlpath.common import Parsers as YPParsers

from .casters import cast_stringy_data
from .converters import (
    mk_json_types_converter, mk_stringy_converter, mk_toml_types_converter, mk_yaml_types_converter
)

try:
    from tomli import load as tload, loads as tloads
    from tomli_w import dumps as _tdumps
except ImportError:
    TOML_SUPPORT = False
else:
    TOML_SUPPORT = True

YAML_EDITOR = YPParsers.get_yaml_editor()
YAML_EDITOR.indent(mapping=2, sequence=4, offset=2)
ydump = YAML_EDITOR.dump
yload = YAML_EDITOR.load

RICH = RichConsole()


def _syntax_print(content: str, syntax: str, console: RichConsole = RICH):
    """
    Print a syntax-highlighted rendering of the content to terminal.

    Args:
        content: Any code to be syntax-highlighted.
        syntax: A syntax name recognized by pygments (via rich).
        console: An initialized Rich Console object used to print with.
    """
    console.print(RichSyntax(content, syntax, theme='ansi_dark'))


def ntdump(data: dict | list):
    """
    Pretty-print the data as NestedText, with color if interactive, to stdout.

    Args:
        data: A ``dict`` or ``list`` to dump as NestedText.
    """
    if sys.stdout.isatty():
        _syntax_print(_ntdumps(data, indent=2), 'nt')
    else:
        _ntdump(data, sys.stdout, indent=2)


def jdump(data: dict | list):
    """
    Pretty-print the data as JSON, with color if interactive, to stdout.

    Args:
        data: A ``dict`` or ``list`` to dump as JSON.
    """
    if sys.stdout.isatty():
        _syntax_print(_jdumps(data, indent=2), 'json')
    else:
        _jdump(data, sys.stdout, indent=2)


def _require_toml_support():
    """
    If TOML support is not installed, raise an exception.

    Raises:
        ImportError: The libraries for TOML support are absent.
    """
    if not TOML_SUPPORT:
        raise ImportError("TOML support for nt2 is not installed. Try reinstalling as 'nt2[toml]'")


def tdump(data: dict):
    """
    Pretty-print the data as TOML, with color if interactive, to stdout.

    Args:
        data: A ``dict`` to dump as TOML.
    """
    _require_toml_support()
    if sys.stdout.isatty():
        _syntax_print(_tdumps(data, multiline_strings=True), 'toml')
    else:
        print(_tdumps(data, multiline_strings=True), end='')


def jloads(content: str) -> dict | list:
    """
    Wrap ``json.loads`` so that on failure it tries parsing as JSON Lines.

    Args:
        content: JSON or JSON Lines content.

    Returns:
        Parsed JSON data as a ``dict`` or ``list`` (usually the former).
    """
    try:
        return _jloads(content)
    except JSONDecodeError:
        return [_jloads(line) for line in content.splitlines()]


def dump_json_to_nestedtext(*input_files):
    r"""
    Read JSON from stdin or ``input_files``, and send NestedText to stdout.

    Args:
        input_files: Usually ``plumbum.local.path``\ s, must have ``read()``,
            containing JSON content.
    """
    # We may need to use a converter.unstructure here; We'll see.
    for f in input_files or (sys.stdin,):
        typed_data = jloads(f.read())
        ntdump(typed_data)


def dump_yaml_to_nestedtext(*input_files):
    r"""
    Read YAML from stdin or ``input_files``, and send NestedText to stdout.

    Args:
        input_files: Usually ``plumbum.local.path``\ s, must be ``open``\ -able,
            containing YAML content.
    """
    converter = mk_stringy_converter()
    if not input_files:
        data = yload(sys.stdin)
        data = converter.unstructure(data)
        ntdump(data)
    else:
        for f in input_files:
            with open(f) as ifile:
                data = yload(ifile)
            data = converter.unstructure(data)
            ntdump(data)


def dump_toml_to_nestedtext(*input_files):
    r"""
    Read TOML from stdin or ``input_files``, and send NestedText to stdout.

    Args:
        input_files: Usually ``plumbum.local.path``\ s, must be ``open``\ -able,
            containing TOML content.
    """
    _require_toml_support()
    converter = mk_stringy_converter()
    if not input_files:
        data = tloads(sys.stdin.read())
        data = converter.unstructure(data)
        ntdump(data)
    else:
        for f in input_files:
            with open(f, 'rb') as ifile:
                data = tload(ifile)
            data = converter.unstructure(data)
            ntdump(data)


def dump_nestedtext_to_yaml(
    *input_files, bool_paths=(), null_paths=(), num_paths=(), date_paths=()
):
    r"""
    Read NestedText from stdin or ``input_files``, and send up-typed YAML to stdout.

    Args:
        input_files: Usually ``plumbum.local.path``\ s, must be suitable for ``nestedtext.load``,
            containing NestedText content.
        bool_paths: YAMLPath queries whose matches will be casted to ``bool``.
        null_paths: YAMLPath queries whose matches will be casted to ``None``.
        num_paths: YAMLPath queries whose matches will be casted to ``int``/``float``.
        date_paths: YAMLPath queries whose matches will be casted to ``date``/``datetime``.
    """
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
    r"""
    Read NestedText from stdin or ``input_files``, and send up-typed TOML to stdout.

    Args:
        input_files: Usually ``plumbum.local.path``\ s, must be suitable for ``nestedtext.load``,
            containing NestedText content.
        bool_paths: YAMLPath queries whose matches will be casted to ``bool``.
        num_paths: YAMLPath queries whose matches will be casted to ``int``/``float``.
        date_paths: YAMLPath queries whose matches will be casted to
            ``date``/``datetime``/``time``.
    """
    _require_toml_support()
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
        tdump(data)


def dump_nestedtext_to_json(*input_files, bool_paths=(), null_paths=(), num_paths=()):
    r"""
    Read NestedText from stdin or ``input_files``, and send up-typed JSON to stdout.

    Args:
        input_files: Usually ``plumbum.local.path``\ s, must be suitable for ``nestedtext.load``,
            containing NestedText content.
        bool_paths: YAMLPath queries whose matches will be casted to ``bool``.
        null_paths: YAMLPath queries whose matches will be casted to ``None``.
        num_paths: YAMLPath queries whose matches will be casted to ``int``/``float``.
    """
    for src in input_files or (sys.stdin,):
        data = ntload(src, 'any')
        data = cast_stringy_data(
            data,
            bool_paths=bool_paths,
            null_paths=null_paths,
            num_paths=num_paths,
            converter=mk_json_types_converter(),
        )
        jdump(data)
