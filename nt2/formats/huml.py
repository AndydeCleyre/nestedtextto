"""Support for HUML."""

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
    from pyhuml import dump as huml_dump, dumps as huml_dumps, load as huml_load
except ImportError:
    HUML_SUPPORT = False
else:
    HUML_SUPPORT = True

if HUML_SUPPORT:
    from pyhuml import HUMLParseError

    from nt2.exceptions import NTTError, NTTError_from, docstring_for_NTTError_from

    @NTTError_from.register
    @docstring_for_NTTError_from
    def NTTError_from_HUMLParseError(exc: HUMLParseError) -> NTTError:  # noqa: N802, D103
        title = "HUML"
        summary = "This HUML couldn't be parsed"
        content = exc.args
        suggestion = "See https://huml.io/ and https://github.com/huml-lang/pyhuml/issues/"
        return NTTError(title=title, summary=summary, content=content, suggestion=suggestion)


require_support = mk_require_support(
    format_name='HUML', supported=HUML_SUPPORT, extras_name='huml'
)


@description_more_for_subcommand  # pyright: ignore [reportArgumentType]
@docstring_for_subcommand  # pyright: ignore [reportArgumentType]
class NestedTextToHUML(SupportsTypes, SupportsNull, SubcommandOfNestedTextTo):  # noqa: D101
    OTHER_FORMAT = "HUML"

    @friendly_exceptions
    @require_support
    def main(self, *NESTED_TEXT_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        self.dump(
            input_files=NESTED_TEXT_FILE,  # pyright: ignore [reportArgumentType]
            dump_stdout=lambda data: huml_dump(data, sys.stdout),  # pyright: ignore [reportPossiblyUnboundVariable]
            dump_str=huml_dumps,  # pyright: ignore [reportPossiblyUnboundVariable]
            fmt='huml',
            converter=mk_json_types_converter(),
        )


@description_more_for_subcommand  # pyright: ignore [reportArgumentType]
@docstring_for_subcommand  # pyright: ignore [reportArgumentType]
class HUMLToNestedText(SubcommandOfToNestedText):  # noqa: D101
    OTHER_FORMAT = "HUML"

    @friendly_exceptions
    @require_support
    def main(self, *HUML_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        self.dump(
            load_stdin=lambda: huml_load(sys.stdin),  # pyright: ignore [reportPossiblyUnboundVariable]
            load_file=lambda input_file: huml_load(input_file),  # pyright: ignore [reportPossiblyUnboundVariable, reportArgumentType]
            input_files=HUML_FILE,
        )


SUBCOMMANDS = {
    'nt2': {'names': ('huml',), 'app': NestedTextToHUML},
    '2nt': {'names': ('huml',), 'app': HUMLToNestedText},
}

EXTENSIONS = ('huml',)
