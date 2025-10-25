"""NestedText format support."""

from __future__ import annotations

import sys
from contextlib import suppress
from typing import TYPE_CHECKING, cast

from nestedtext import (
    NestedTextError,
    dump as nestedtext_dump,
    dumps as nestedtext_dumps,
    load as nestedtext_load,
)
from plumbum import local
from plumbum.colors import magenta  # pyright: ignore [reportAttributeAccessIssue]

from nt2.exceptions import NTTError, NTTError_from, docstring_for_NTTError_from

if TYPE_CHECKING:
    from typing import TextIO

    from plumbum import LocalPath

    from nt2.types import JSONData, StringyData


# nt2 hjson test/samples/json/base.nt -s test/samples/json/typed_all.json
# ╭─────────────────────── <class 'nestedtext.nestedtext.NestedTextError'> ───────────────────────╮
# │ The *load* and *dump* functions all raise *NestedTextError* when they                         │
# │ discover an error. *NestedTextError* subclasses both the Python *ValueError*                  │
# │ and the *Error* exception from *Inform*.  You can find more documentation on                  │
# │ what you can do with this exception in the `Inform documentation                              │
# │ <https://inform.readthedocs.io/en/stable/api.html#exceptions>`_.                              │
# │                                                                                               │
# │   args = ()                                                                                   │
# │ kwargs = {                                                                                    │
# │              'template': 'line ended without closing delimiter.',                             │
# │              'culprit': (                                                                     │
# │                  '/home/andy/Code/nestedtextto/test/samples/json/typed_all.json',             │
# │                  1                                                                            │
# │              ),                                                                               │
# │              'suppress_prev_line': True,                                                      │
# │              'source': '/home/andy/Code/nestedtextto/test/samples/json/typed_all.json',       │
# │              'codicil': ('   1 ❬{❭\n       ▲',),                                              │
# │              'colno': 1,                                                                      │
# │              'line': '{',                                                                     │
# │              'lineno': 0                                                                      │
# │          }                                                                                    │
# ╰───────────────────────────────────────────────────────────────────────────────────────────────╯


@NTTError_from.register
@docstring_for_NTTError_from
def NTTError_from_NestedTextError(exc: NestedTextError) -> NTTError:  # noqa: N802, D103
    title = "NestedText"
    summary = "This NestedText couldn't be parsed"
    src = exc.source or ""
    if src:
        src_file = local.path(src)
        if src_file.exists():
            src = src_file.relative_to(local.cwd)
        src = f"{src}:{exc.lineno}:{exc.colno}"
    content = (exc.line, f"{'.' * (exc.colno - 1)}▲" | magenta, exc.get_message())
    with suppress(AttributeError):
        content = (exc.prev_line, *content)
    suggestion = "See https://nestedtext.org/en/latest/basic_syntax.html"
    return NTTError(
        title=title,
        summary=summary,
        file=src,
        content=content,  # pyright: ignore [reportArgumentType]
        suggestion=suggestion,
    )


def dump_stdout(data: JSONData, inline_width: int = 0):
    """
    Print the data as NestedText, without color, to stdout.

    Args:
        data: A ``JSONData`` to dump as NestedText.
        inline_width: Maximum line length for inline dictionaries and lists.
    """
    nestedtext_dump(data, sys.stdout, indent=2, width=inline_width)


def dump_str(data: JSONData, inline_width: int = 0) -> str:
    """
    Return a string representation of the data as NestedText, without color.

    Args:
        data: A ``JSONData`` to dump as NestedText.
        inline_width: Maximum line length for inline dictionaries and lists.

    Returns:
        A string representation of the data as NestedText.
    """
    return nestedtext_dumps(data, indent=2, width=inline_width)


def load(file: str | LocalPath | TextIO) -> StringyData:
    """
    Wrap ``nestedtext.load`` with convenient configuration.

    Set top-level type constraint to 'any',
    and assure the type checker the result is ``StringyData``.

    Args:
        file: NestedText file-like object, usually a ``LocalPath`` or ``sys.stdin``.

    Returns:
        Parsed NestedText data as ``StringyData``.
    """
    return cast('StringyData', nestedtext_load(file, top='any'))
