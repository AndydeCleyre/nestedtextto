"""Main functions to be called by the UI Application classes, after CLI option parsing."""

from __future__ import annotations

import io
import sys
from json import dump as _jdump, dumps as _jdumps, loads as _jloads
from json.decoder import JSONDecodeError
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from plumbum import LocalPath
from os import environ
from textwrap import indent
from typing import BinaryIO, Sequence, TextIO, cast

from nestedtext import dump as _ntdump, dumps as _ntdumps, load as _ntload
from rich.console import Console as RichConsole
from rich.syntax import Syntax as RichSyntax
from ruamel.yaml.scalarstring import walk_tree as use_multiline_syntax

from .casters import StringyData, cast_stringy_data
from .converters import (
    mk_json_types_converter,
    mk_stringy_converter,
    mk_toml_types_converter,
    # mk_huml_types_converter,
    mk_yaml_types_converter,
)
from .yamlpath_tools import guess_briefer_schema, mk_yaml_editor, typed_data_to_schema

try:
    from tomli import load as tload, loads as tloads
    from tomli_w import dumps as _tdumps
except ImportError:
    TOML_SUPPORT = False
else:
    TOML_SUPPORT = True

try:
    from pyhuml import dump as _huml_dump, dumps as _huml_dumps, load as huml_load
except ImportError:
    HUML_SUPPORT = False
else:
    HUML_SUPPORT = True

YAML_EDITOR = mk_yaml_editor()
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
    console.print(
        RichSyntax(
            content,
            syntax,
            theme='ansi_dark',
            word_wrap=True,
            indent_guides=not environ.get('NO_COLOR'),
        )
    )


def ntload(file: str | Path | TextIO) -> StringyData:
    r"""
    Wrap ``nestedtext.load`` with convenient configuration for this module.

    Set top-level type constraint to 'any',
    and assure the type checker the result is ``StringyData``.

    Args:
        file: NestedText file-like object, usually a ``LocalPath`` or ``sys.stdin``.

    Returns:
        Parsed NestedText data as a ``str``, ``dict``, or ``list``.
    """
    return cast(StringyData, _ntload(file, top='any'))


def ntdump(data: dict | list | str):
    """
    Pretty-print the data as NestedText, with color if interactive, to stdout.

    Args:
        data: A ``dict``, ``list``, or ``str`` to dump as NestedText.
    """
    if sys.stdout.isatty():
        _syntax_print(_ntdumps(data, indent=2), 'nt')
    else:
        _ntdump(data, sys.stdout, indent=2)


def jdump(data: dict | list | str):
    """
    Pretty-print the data as JSON, with color if interactive, to stdout.

    Args:
        data: A ``dict``, ``list``, or ``str`` to dump as JSON.
    """
    if sys.stdout.isatty():
        _syntax_print(_jdumps(data, indent=2), 'json')
    else:
        _jdump(data, sys.stdout, indent=2)


# TODO: ydump string input?
def ydump(data: dict | list):
    """
    Pretty-print the data as YAML, with color if interactive, to stdout.

    Args:
        data: A ``dict`` or ``list`` to dump as YAML.

    Raises:
        Exception: Unexpected problem dumping or highlighting data.
    """
    use_multiline_syntax(data)
    if sys.stdout.isatty():
        out_stream = io.StringIO()
        try:
            YAML_EDITOR.dump(data, out_stream)
        except Exception:
            raise
        else:
            _syntax_print(out_stream.getvalue(), 'yaml')
        finally:
            out_stream.close()
    else:
        YAML_EDITOR.dump(data, sys.stdout)


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
        _syntax_print(_tdumps(data, multiline_strings=True), 'toml')  # pyright: ignore [reportPossiblyUnboundVariable]
    else:
        print(_tdumps(data, multiline_strings=True), end='')  # pyright: ignore [reportPossiblyUnboundVariable]


def _require_huml_support():
    """
    If HUML support is not installed, raise an exception.

    Raises:
        ImportError: The libraries for HUML support are absent.
    """
    if not HUML_SUPPORT:
        raise ImportError("HUML support for nt2 is not installed. Try reinstalling as 'nt2[huml]'")


def huml_dump(data: dict | list | str):
    """
    Pretty-print the data as HUML, with color if interactive, to stdout.

    Args:
        data: A ``dict``, ``list``, or ``str`` to dump as HUML.
    """
    _require_huml_support()
    if sys.stdout.isatty():
        _syntax_print(_huml_dumps(data), 'huml')  # pyright: ignore [reportPossiblyUnboundVariable]
    else:
        _huml_dump(data, sys.stdout)  # pyright: ignore [reportPossiblyUnboundVariable]


def jloads(content: str) -> dict | list:
    """
    Wrap ``json.loads`` so that on failure it tries parsing as JSON Lines.

    Args:
        content: JSON or JSON Lines content.

    Returns:
        Parsed JSON data as a ``dict`` or ``list`` (usually the former).

    Raises:
        JSONDecodeError: Unable to parse ``content`` as JSON or JSONLines.

    # noqa: DAR401
    # noqa: DAR402
    """
    try:
        return _jloads(content)
    except JSONDecodeError as original_e:
        try:
            return [_jloads(line) for line in content.splitlines()]
        except JSONDecodeError:  # pragma: no cover
            raise original_e from None


def dump_json_to_nestedtext(*input_files: LocalPath):
    r"""
    Read JSON from stdin or ``input_files``, and send NestedText to stdout.

    Args:
        input_files: ``LocalPath``\ s with JSON content.
    """
    # We may need to use a converter.unstructure here; We'll see.
    if not input_files:
        typed_data = jloads(sys.stdin.read())
        ntdump(typed_data)
    else:
        for f in input_files:
            typed_data = jloads(f.read('utf-8'))
            ntdump(typed_data)


def _dump_typed_data_to_schema(typed_data: dict | list | str):
    if isinstance(typed_data, str):
        print()
        return

    schema = typed_data_to_schema(typed_data)
    ntdump(schema)

    briefer_schema = guess_briefer_schema(schema)
    if sum(len(path_list) for path_list in briefer_schema.values()) < sum(
        len(path_list) for path_list in schema.values()
    ):
        content = '\n'.join(
            (
                '',
                '# Above is a schema that literally matches the current data.',
                '# Below, for your review, is a guess at a better schema.',
                '',
                indent(_ntdumps(briefer_schema, indent=2), '# '),
            )
        )
        if sys.stdout.isatty():
            _syntax_print(content, 'nt')
        else:
            print(content)


def dump_json_to_schema(*input_files: LocalPath):
    r"""
    Read JSON from stdin or ``input_files``, and send a NestedText schema to stdout.

    Args:
        input_files: ``LocalPath``\ s with JSON content.
    """
    if not input_files:
        typed_data = jloads(sys.stdin.read())
        _dump_typed_data_to_schema(typed_data)
    else:
        for f in input_files:
            typed_data = jloads(f.read('utf-8'))
            _dump_typed_data_to_schema(typed_data)


def dump_yaml_to_schema(*input_files: LocalPath):
    r"""
    Read YAML from stdin or ``input_files``, and send a NestedText schema to stdout.

    Args:
        input_files: ``LocalPath``\ s with YAML content.
    """
    if not input_files:
        typed_data = yload(sys.stdin)
        _dump_typed_data_to_schema(typed_data)
    else:
        for f in input_files:
            with f.open(encoding='utf-8') as ifile:
                typed_data = yload(ifile)
            _dump_typed_data_to_schema(typed_data)


def dump_toml_to_schema(*input_files: LocalPath):
    r"""
    Read TOML from stdin or ``input_files``, and send a NestedText schema to stdout.

    Args:
        input_files: ``LocalPath``\ s with TOML content.
    """
    _require_toml_support()
    if not input_files:
        typed_data = tloads(sys.stdin.read())  # pyright: ignore [reportPossiblyUnboundVariable]
        _dump_typed_data_to_schema(typed_data)
    else:
        for f in input_files:
            with f.open('rb') as ifile:
                typed_data = tload(cast(BinaryIO, ifile))  # pyright: ignore [reportPossiblyUnboundVariable]
            _dump_typed_data_to_schema(typed_data)


def dump_huml_to_schema(*input_files: LocalPath):
    r"""
    Read HUML from stdin or ``input_files``, and send a NestedText schema to stdout.

    Args:
        input_files: ``LocalPath``\ s with HUML content.
    """
    _require_huml_support()
    if not input_files:
        typed_data = huml_load(sys.stdin)  # pyright: ignore [reportPossiblyUnboundVariable]
        _dump_typed_data_to_schema(typed_data)
    else:
        for f in input_files:
            typed_data = huml_load(f)  # pyright: ignore [reportPossiblyUnboundVariable,reportArgumentType]
            _dump_typed_data_to_schema(typed_data)


def dump_yaml_to_nestedtext(*input_files: LocalPath):
    r"""
    Read YAML from stdin or ``input_files``, and send NestedText to stdout.

    Args:
        input_files: ``LocalPath``\ s with YAML content.
    """
    converter = mk_stringy_converter()
    if not input_files:
        data = yload(sys.stdin)
        data = converter.unstructure(data)
        ntdump(data)
    else:
        for f in input_files:
            with f.open(encoding='utf-8') as ifile:
                data = yload(ifile)
            data = converter.unstructure(data)
            ntdump(data)


def dump_toml_to_nestedtext(*input_files: LocalPath):
    r"""
    Read TOML from stdin or ``input_files``, and send NestedText to stdout.

    Args:
        input_files: ``LocalPath``\ s with TOML content.
    """
    _require_toml_support()
    converter = mk_stringy_converter()
    if not input_files:
        data = tloads(sys.stdin.read())  # pyright: ignore [reportPossiblyUnboundVariable]
        data = converter.unstructure(data)
        ntdump(data)
    else:
        for f in input_files:
            with f.open('rb') as ifile:
                data = tload(cast(BinaryIO, ifile))  # pyright: ignore [reportPossiblyUnboundVariable]
            data = converter.unstructure(data)
            ntdump(data)


def dump_huml_to_nestedtext(*input_files: LocalPath):
    r"""
    Read HUML from stdin or ``input_files``, and send NestedText to stdout.

    Args:
        input_files: ``LocalPath``\ s with HUML content.
    """
    _require_huml_support()
    converter = mk_stringy_converter()
    if not input_files:
        data = huml_load(sys.stdin)  # pyright: ignore [reportPossiblyUnboundVariable]
        data = converter.unstructure(data)
        ntdump(data)
    else:
        for f in input_files:
            data = huml_load(f)  # pyright: ignore [reportPossiblyUnboundVariable,reportArgumentType]
            data = converter.unstructure(data)
            ntdump(data)


def dump_nestedtext_to_yaml(
    *input_files: LocalPath,
    bool_paths: Sequence[str] = (),
    null_paths: Sequence[str] = (),
    num_paths: Sequence[str] = (),
    date_paths: Sequence[str] = (),
):
    r"""
    Read NestedText from stdin or ``input_files``, and send up-typed YAML to stdout.

    Args:
        input_files: ``LocalPath``\ s with NestedText content.
        bool_paths: YAMLPath queries whose matches will be casted to ``bool``.
        null_paths: YAMLPath queries whose matches will be casted to ``None``.
        num_paths: YAMLPath queries whose matches will be casted to ``int``/``float``.
        date_paths: YAMLPath queries whose matches will be casted to ``date``/``datetime``.
    """
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
        ydump(data)


def dump_nestedtext_to_toml(
    *input_files: LocalPath,
    bool_paths: Sequence[str] = (),
    num_paths: Sequence[str] = (),
    date_paths: Sequence[str] = (),
):
    r"""
    Read NestedText from stdin or ``input_files``, and send up-typed TOML to stdout.

    Args:
        input_files: ``LocalPath``\ s with NestedText content.
        bool_paths: YAMLPath queries whose matches will be casted to ``bool``.
        num_paths: YAMLPath queries whose matches will be casted to ``int``/``float``.
        date_paths: YAMLPath queries whose matches will be casted to
            ``date``/``datetime``/``time``.
    """
    _require_toml_support()
    for src in input_files or (sys.stdin,):
        data = ntload(src)
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


def dump_nestedtext_to_json(
    *input_files: LocalPath,
    bool_paths: Sequence[str] = (),
    null_paths: Sequence[str] = (),
    num_paths: Sequence[str] = (),
):
    r"""
    Read NestedText from stdin or ``input_files``, and send up-typed JSON to stdout.

    Args:
        input_files: ``LocalPath``\ s with NestedText content.
        bool_paths: YAMLPath queries whose matches will be casted to ``bool``.
        null_paths: YAMLPath queries whose matches will be casted to ``None``.
        num_paths: YAMLPath queries whose matches will be casted to ``int``/``float``.
    """
    for src in input_files or (sys.stdin,):
        data = ntload(src)
        data = cast_stringy_data(
            data,
            bool_paths=bool_paths,
            null_paths=null_paths,
            num_paths=num_paths,
            converter=mk_json_types_converter(),
        )
        jdump(data)


def dump_nestedtext_to_huml(
    *input_files: LocalPath,
    bool_paths: Sequence[str] = (),
    null_paths: Sequence[str] = (),
    num_paths: Sequence[str] = (),
):
    r"""
    Read NestedText from stdin or ``input_files``, and send up-typed HUML to stdout.

    Args:
        input_files: ``LocalPath``\ s with NestedText content.
        bool_paths: YAMLPath queries whose matches will be casted to ``bool``.
        null_paths: YAMLPath queries whose matches will be casted to ``None``.
        num_paths: YAMLPath queries whose matches will be casted to ``int``/``float``.
    """
    _require_huml_support()
    for src in input_files or (sys.stdin,):
        data = ntload(src)
        data = cast_stringy_data(
            data,
            bool_paths=bool_paths,
            null_paths=null_paths,
            num_paths=num_paths,
            converter=mk_json_types_converter(),
            # TODO: we may need a new converter, especially to handle number syntaxes
        )
        huml_dump(data)
