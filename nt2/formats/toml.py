"""Support for TOML."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, cast

from plumbum.cli import ExistingFile  # noqa: TC002

from nt2.commands import (
    SubcommandOfNestedTextTo,
    SubcommandOfToNestedText,
    SupportsDate,
    SupportsTypes,
    description_more_for_subcommand,
    docstring_for_subcommand,
)
from nt2.converters import mk_toml_types_converter
from nt2.exceptions import friendly_exceptions, mk_require_support

if TYPE_CHECKING:
    from typing import BinaryIO

    from plumbum import LocalPath

    from nt2.types import TOMLData, TOMLHashData


try:
    from tomli import load as toml_load, loads as toml_loads
    from tomli_w import dumps as toml_dumps
except ImportError:
    TOML_SUPPORT = False
else:
    TOML_SUPPORT = True

if TOML_SUPPORT:
    from tomli import TOMLDecodeError

    from nt2.exceptions import NTTError, NTTError_from, docstring_for_NTTError_from

    @NTTError_from.register
    @docstring_for_NTTError_from
    def NTTError_from_TOMLDecodeError(exc: TOMLDecodeError) -> NTTError:  # noqa: N802, D103
        title = "TOML"
        summary = "This TOML couldn't be parsed"
        content = exc.args
        return NTTError(title=title, summary=summary, content=content)


require_support = mk_require_support(
    format_name='TOML', supported=TOML_SUPPORT, extras_name='toml'
)


def _load_file(input_file: LocalPath) -> TOMLData:
    """
    Read TOML from input_file and return typed data.

    Args:
        input_file: ``LocalPath`` with TOML content.

    Returns:
        The TOML data.
    """
    with input_file.open('rb') as ifile:
        return toml_load(cast('BinaryIO', ifile))  # pyright: ignore [reportPossiblyUnboundVariable]


def _fix_data(data: TOMLData) -> TOMLHashData:
    """
    Force the data to be a top-level hash table.

    Args:
        data: TOML data.

    Returns:
        The data as a top-level hash table.
    """
    if not isinstance(data, dict):
        return {'root': data}
    return data


@description_more_for_subcommand  # pyright: ignore [reportArgumentType]
@docstring_for_subcommand  # pyright: ignore [reportArgumentType]
class NestedTextToTOML(SupportsTypes, SupportsDate, SubcommandOfNestedTextTo):  # noqa: D101
    OTHER_FORMAT = "TOML"

    @friendly_exceptions
    @require_support
    def main(self, *NESTED_TEXT_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        self.dump(
            input_files=NESTED_TEXT_FILE,  # pyright: ignore [reportArgumentType]
            dump_stdout=lambda data: print(toml_dumps(data, multiline_strings=True), end=''),  # pyright: ignore [reportPossiblyUnboundVariable, reportArgumentType]
            dump_str=lambda data: toml_dumps(data, multiline_strings=True),  # pyright: ignore [reportPossiblyUnboundVariable, reportArgumentType]
            fmt='toml',
            converter=mk_toml_types_converter(),
            fix_data=_fix_data,  # pyright: ignore [reportArgumentType]
        )


@description_more_for_subcommand  # pyright: ignore [reportArgumentType]
@docstring_for_subcommand  # pyright: ignore [reportArgumentType]
class TOMLToNestedText(SubcommandOfToNestedText):  # noqa: D101
    OTHER_FORMAT = "TOML"

    @friendly_exceptions
    @require_support
    def main(self, *TOML_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        self.dump(
            load_stdin=lambda: toml_loads(sys.stdin.read()),  # pyright: ignore [reportPossiblyUnboundVariable]
            load_file=_load_file,
            input_files=TOML_FILE,
        )


SUBCOMMANDS = {
    'nt2': {'names': ('toml',), 'app': NestedTextToTOML},
    '2nt': {'names': ('toml',), 'app': TOMLToNestedText},
}

EXTENSIONS = ('toml',)
