"""Support for MAML."""

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
    from maml import dump as maml_dump, dumps as maml_dumps, load as maml_load
except ImportError:
    MAML_SUPPORT = False
else:
    MAML_SUPPORT = True


if MAML_SUPPORT:
    from maml import MAMLSyntaxError

    from nt2.exceptions import NTTError, NTTError_from, docstring_for_NTTError_from

    @NTTError_from.register
    @docstring_for_NTTError_from
    def NTTError_from_MAMLSyntaxError(exc: MAMLSyntaxError) -> NTTError:  # noqa: N802, D103
        title = "MAML"
        summary = "This MAML couldn't be parsed"
        src = f"{exc.line}:{exc.column}"
        content = (exc.message,)
        suggestion = "See https://maml.dev/ and https://gitlab.com/matdevdug/maml-py/-/issues"
        return NTTError(
            title=title, summary=summary, file=src, content=content, suggestion=suggestion
        )


require_support = mk_require_support(
    format_name='MAML', supported=MAML_SUPPORT, extras_name='maml'
)


@description_more_for_subcommand  # pyright: ignore [reportArgumentType]
@docstring_for_subcommand  # pyright: ignore [reportArgumentType]
class NestedTextToMAML(SupportsTypes, SupportsNull, SubcommandOfNestedTextTo):  # noqa: D101
    OTHER_FORMAT = "MAML"

    @friendly_exceptions
    @require_support
    def main(self, *NESTED_TEXT_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        self.dump(
            input_files=NESTED_TEXT_FILE,  # pyright: ignore [reportArgumentType]
            dump_stdout=lambda data: maml_dump(data, sys.stdout),  # pyright: ignore [reportPossiblyUnboundVariable]
            dump_str=maml_dumps,  # pyright: ignore [reportPossiblyUnboundVariable]
            fmt='maml',
            converter=mk_json_types_converter(),
        )


@description_more_for_subcommand  # pyright: ignore [reportArgumentType]
@docstring_for_subcommand  # pyright: ignore [reportArgumentType]
class MAMLToNestedText(SubcommandOfToNestedText):  # noqa: D101
    OTHER_FORMAT = "MAML"

    @friendly_exceptions
    @require_support
    def main(self, *MAML_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        self.dump(
            load_stdin=lambda: maml_load(sys.stdin),  # pyright: ignore [reportPossiblyUnboundVariable]
            load_file=lambda input_file: maml_load(input_file),  # pyright: ignore [reportPossiblyUnboundVariable, reportArgumentType]
            input_files=MAML_FILE,
        )


SUBCOMMANDS = {
    'nt2': {'app': NestedTextToMAML, 'names': ('maml',)},
    '2nt': {'app': MAMLToNestedText, 'names': ('maml',)},
}

EXTENSIONS = ('maml',)
