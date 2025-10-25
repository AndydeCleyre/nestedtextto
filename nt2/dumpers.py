"""Main functions to be called by the UI Application classes, after CLI option parsing."""

from __future__ import annotations

import sys
from os import environ
from textwrap import indent
from typing import TYPE_CHECKING

from rich.console import Console as RichConsole
from rich.syntax import Syntax as RichSyntax

from .casters import cast_stringy_data
from .converters import mk_stringy_converter
from .formats import nestedtext
from .yamlpath_tools import guess_briefer_schema, typed_data_to_schema

if TYPE_CHECKING:
    from typing import Any, Callable, Sequence

    from cattrs import Converter
    from plumbum import LocalPath

    from .types import TypedData

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


def _ansi_ok() -> bool:
    """
    Return ``True`` if it's acceptable to use ANSI escape sequences.

    Returns:
        ``True`` if stdout is a terminal OR ``FORCE_COLOR`` is set.
    """
    return bool(sys.stdout.isatty() or environ.get('FORCE_COLOR'))


def dump_format(
    *,
    data: TypedData,
    fmt: str,
    dump_stdout: Callable[[TypedData], None],
    dump_str: Callable[[TypedData], str],
    **kwargs: Any,
):
    """
    Pretty-print the data as fmt, with color if interactive, to stdout.

    Args:
        data: ``TypedData`` to dump as the format.
        fmt: The format to dump as (e.g. 'json').
        dump_stdout: A function to dump the data to stdout, plainly.
        dump_str: A function to dump the data to a string, also plain, for potential colorizing.
        **kwargs: Keyword arguments to pass to the format's ``dump_str`` or ``dump_stdout``.
    """
    if _ansi_ok():
        _syntax_print(dump_str(data, **kwargs), fmt)
    else:
        dump_stdout(data, **kwargs)


def _dump_to_nestedtext(data: TypedData, *, inline_width: int = 0):
    """
    Pretty-print the data as NestedText, with color if interactive, to stdout.

    Args:
        data: An object, usually ``dict`` or ``list``, to dump as NestedText.
        inline_width: Maximum line length for inline dictionaries and lists.
    """
    # TODO: is it worth anything to skip the unstructuring with a flag, for performance,
    #   for JSONData?

    dump_format(
        data=mk_stringy_converter().unstructure(data),
        fmt='nt',
        dump_stdout=nestedtext.dump_stdout,  # pyright: ignore [reportArgumentType]
        dump_str=nestedtext.dump_str,  # pyright: ignore [reportArgumentType]
        inline_width=inline_width,
    )


def _dump_typed_data_to_schema(typed_data: TypedData):
    schema = typed_data_to_schema(typed_data)
    _dump_to_nestedtext(schema)

    if not schema:
        return

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
                indent(nestedtext.dump_str(briefer_schema), '# '),
            )
        )
        if _ansi_ok():
            _syntax_print(content, 'nt')
        else:
            print(content)


# TODO: do I want to be passing around full Converters, or just their unstructure functions?
def dump_from_nestedtext(  # noqa: PLR0913
    *,
    input_files: LocalPath,
    dump_stdout: Callable[[TypedData], None],
    dump_str: Callable[[TypedData], str],
    fmt: str,
    converter: Converter,
    fix_data: Callable[[TypedData], TypedData] | None = None,
    # hmmm:
    bool_paths: Sequence[str] = (),
    null_paths: Sequence[str] = (),
    num_paths: Sequence[str] = (),
    date_paths: Sequence[str] = (),
):
    r"""
    Read NestedText from stdin or ``input_files``, and send an up-typed data format to stdout.

    Args:
        input_files: ``LocalPath``\ s with NestedText content.
        dump_stdout: A function to dump the data to stdout, plainly.
        dump_str: A function to dump the data to a string, also plain, for potential colorizing.
        fmt: The format to use for dumping (e.g., 'toml').
        converter: A ``Converter`` used to ``unstructure`` the result
            to match specific type support.
        fix_data: A function to fix the data, post-uptyping, if necessary.
        bool_paths: YAMLPath queries whose matches will be up-typed to ``bool``.
        null_paths: YAMLPath queries whose matches will be up-typed to ``None``.
        num_paths: YAMLPath queries whose matches will be up-typed to ``int``/``float``.
        date_paths: YAMLPath queries whose matches will be up-typed to
            ``date``/``datetime``/``time``.
    """
    nt_data_objects = [nestedtext.load(f) for f in (input_files or (sys.stdin,))]
    for d in nt_data_objects:
        data = cast_stringy_data(
            d,
            bool_paths=bool_paths,
            null_paths=null_paths,
            num_paths=num_paths,
            date_paths=date_paths,
            # TODO: yamlpaths... maybe collected in paths_kwargs?
            converter=converter,
        )
        if fix_data:
            data = fix_data(data)
        dump_format(data=data, fmt=fmt, dump_stdout=dump_stdout, dump_str=dump_str)


def dump_to_nestedtext(
    *,
    load_stdin: Callable[[], TypedData],
    load_file: Callable[[LocalPath], TypedData],
    input_files: Sequence[LocalPath],
    inline_width: int = 0,
):
    r"""
    Read typed data from stdin or ``input_files``, and send NestedText to stdout.

    Colorize if stdout is a terminal.

    Args:
        input_files: ``LocalPath``\ s with typed data content.
        load_stdin: A function to load typed data from stdin.
        load_file: A function to load typed data from a ``LocalPath``.
        inline_width: Maximum line length for inline dictionaries and lists.
    """
    typed_data_objects = [load_file(f) for f in input_files] or (load_stdin(),)
    for d in typed_data_objects:
        _dump_to_nestedtext(d, inline_width=inline_width)


def dump_to_schema(
    *,
    load_stdin: Callable[[], TypedData],
    load_file: Callable[[LocalPath], TypedData],
    input_files: Sequence[LocalPath],
):
    r"""
    Read typed data from stdin or ``input_files``, and send a NestedText schema to stdout.

    Args:
        input_files: ``LocalPath``\ s with typed data content.
        load_stdin: A function to load typed data from stdin.
        load_file: A function to load typed data from a ``LocalPath``.
    """
    if not input_files:
        typed_data = load_stdin()
        _dump_typed_data_to_schema(typed_data)
    else:
        for f in input_files:
            typed_data = load_file(f)
            _dump_typed_data_to_schema(typed_data)
