"""Support for Hjson."""

from __future__ import annotations

import sys

from plumbum.cli import ExistingFile  # noqa: TC002

from nt2.commands import (
    SubcommandOfNestedTextTo,
    SubcommandOfToNestedText,
    SupportsNull,
    SupportsTypes,
    description_more_for_subcommand,
    docstring_for_subcommand,
)
from nt2.converters import mk_json_types_converter
from nt2.exceptions import friendly_exceptions, mk_require_support

try:
    from hjson import dump as hjson_dump, dumps as hjson_dumps, load as hjson_load
except ImportError:
    HJSON_SUPPORT = False
else:
    HJSON_SUPPORT = True

if HJSON_SUPPORT:
    from hjson import HjsonDecodeError

    from nt2.exceptions import NTTError, NTTError_from, docstring_for_NTTError_from

    @NTTError_from.register
    @docstring_for_NTTError_from
    def NTTError_from_HjsonDecodeError(exc: HjsonDecodeError) -> NTTError:  # noqa: N802, D103
        title = "Hjson"
        summary = "This Hjson couldn't be parsed"
        src = f"{exc.lineno}:{exc.colno}"
        if exc.endlineno:
            src += f"-{exc.endlineno}"
            if exc.endcolno:
                src += f":{exc.endcolno}"
        content = (*exc.doc.splitlines()[exc.lineno : (exc.endlineno or exc.lineno + 2)], exc.msg)
        suggestion = "See https://learnxinyminutes.com/hjson"
        return NTTError(
            title=title,
            summary=summary,
            file=src,
            content=content,  # pyright: ignore [reportArgumentType]
            suggestion=suggestion,
        )


require_support = mk_require_support(
    format_name='Hjson', supported=HJSON_SUPPORT, extras_name='hjson'
)


@description_more_for_subcommand  # pyright: ignore [reportArgumentType]
@docstring_for_subcommand  # pyright: ignore [reportArgumentType]
class NestedTextToHjson(SupportsTypes, SupportsNull, SubcommandOfNestedTextTo):  # noqa: D101
    OTHER_FORMAT = "Hjson"

    @friendly_exceptions
    @require_support
    def main(self, *NESTED_TEXT_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        self.dump(
            input_files=NESTED_TEXT_FILE,  # pyright: ignore [reportArgumentType]
            dump_stdout=lambda data: hjson_dump(data, sys.stdout),  # pyright: ignore [reportPossiblyUnboundVariable]
            dump_str=hjson_dumps,  # pyright: ignore [reportPossiblyUnboundVariable]
            fmt='hjson',
            converter=mk_json_types_converter(),
        )


@description_more_for_subcommand  # pyright: ignore [reportArgumentType]
@docstring_for_subcommand  # pyright: ignore [reportArgumentType]
class HjsonToNestedText(SubcommandOfToNestedText):  # noqa: D101
    OTHER_FORMAT = "Hjson"

    @friendly_exceptions
    @require_support
    def main(self, *HJSON_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        self.dump(
            load_stdin=lambda: hjson_load(sys.stdin),  # pyright: ignore [reportPossiblyUnboundVariable]
            load_file=lambda input_file: hjson_load(input_file),  # pyright: ignore [reportPossiblyUnboundVariable]
            input_files=HJSON_FILE,
        )


SUBCOMMANDS = {
    'nt2': {'names': ('hjson',), 'app': NestedTextToHjson},
    '2nt': {'names': ('hjson',), 'app': HjsonToNestedText},
}

EXTENSIONS = ('hjson',)
