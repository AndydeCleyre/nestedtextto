"""Support for JSON."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from plumbum.cli import ExistingFile  # noqa: TC002
from plumbum.colors import magenta  # pyright: ignore [reportAttributeAccessIssue]

from nt2.commands import (
    SubcommandOfNestedTextTo,
    SubcommandOfToNestedText,
    SupportsNull,
    SupportsTypes,
    description_more_for_subcommand,
    docstring_for_subcommand,
)
from nt2.converters import mk_json_types_converter
from nt2.exceptions import (
    NTTError,
    NTTError_from,
    docstring_for_NTTError_from,
    friendly_exceptions,
)

if TYPE_CHECKING:
    from nt2.types import JSONData
from json import dump as json_dump, dumps as json_dumps, loads as json_loads
from json.decoder import JSONDecodeError


@NTTError_from.register
@docstring_for_NTTError_from
def NTTError_from_JSONDecodeError(exc: JSONDecodeError) -> NTTError:  # noqa: N802, D103
    title = "JSON"
    summary = "This JSON couldn't be parsed"
    src = f"{exc.lineno}:{exc.colno}"
    content = (
        *exc.doc.splitlines()[exc.lineno : exc.lineno + 2],
        f"{'.' * (exc.colno - 1)}▲" | magenta,
        exc.msg,
    )
    suggestion = "See https://learnxinyminutes.com/json"
    return NTTError(
        title=title,
        summary=summary,
        file=src,
        content=content,  # pyright: ignore [reportArgumentType]
        suggestion=suggestion,
    )


def _json_loads(content: str) -> JSONData:
    """
    Wrap ``json.loads`` so that on failure it tries parsing as JSON Lines.

    Args:
        content: JSON or JSON Lines content.

    Returns:
        Parsed JSON data as a JSON-supported type, usually ``dict`` or ``list``.

    Raises:
        JSONDecodeError: Unable to parse ``content`` as JSON or JSONLines.

    # noqa: DAR401
    # noqa: DAR402
    """
    try:
        return json_loads(content)
    except JSONDecodeError as original_e:
        try:
            return [json_loads(line) for line in content.splitlines()]
        except JSONDecodeError:
            raise original_e from None


@description_more_for_subcommand  # pyright: ignore [reportArgumentType]
@docstring_for_subcommand  # pyright: ignore [reportArgumentType]
class NestedTextToJSON(SupportsTypes, SupportsNull, SubcommandOfNestedTextTo):  # noqa: D101
    OTHER_FORMAT = "JSON"

    @friendly_exceptions  # pyright: ignore [reportCallIssue]
    def main(self, *NESTED_TEXT_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        self.dump(
            input_files=NESTED_TEXT_FILE,  # pyright: ignore [reportArgumentType]
            dump_stdout=lambda data: json_dump(data, sys.stdout, indent=2),
            dump_str=lambda data: json_dumps(data, indent=2),
            fmt='json',
            converter=mk_json_types_converter(),
        )


@description_more_for_subcommand  # pyright: ignore [reportArgumentType]
@docstring_for_subcommand  # pyright: ignore [reportArgumentType]
class JSONToNestedText(SubcommandOfToNestedText):  # noqa: D101
    OTHER_FORMAT = "JSON"

    @friendly_exceptions
    def main(self, *JSON_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        self.dump(
            load_stdin=lambda: _json_loads(sys.stdin.read()),
            load_file=lambda input_file: _json_loads(input_file.read('utf-8')),
            input_files=JSON_FILE,
        )


SUBCOMMANDS = {
    'nt2': {'app': NestedTextToJSON, 'names': ('json',)},
    '2nt': {'app': JSONToNestedText, 'names': ('json',)},
}

EXTENSIONS = ('json', 'jsonl')
