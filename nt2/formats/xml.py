"""Support for Hjson."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from plumbum import local
from plumbum.cli import ExistingFile  # noqa: TC002

from nt2.commands import (
    SubcommandOfNestedTextTo,
    SubcommandOfToNestedText,
    description_more_for_subcommand,
    docstring_for_subcommand,
)
from nt2.converters import mk_json_types_converter
from nt2.exceptions import friendly_exceptions, mk_require_support

if TYPE_CHECKING:
    from plumbum import LocalPath

    from nt2.types import TypedData
try:
    from xmltodict import parse as xml_parse, unparse as xml_unparse
except ImportError:
    XML_SUPPORT = False
else:
    XML_SUPPORT = True

if XML_SUPPORT:
    from xml.parsers.expat import ExpatError

    from nt2.exceptions import NTTError, NTTError_from, docstring_for_NTTError_from

    @NTTError_from.register
    @docstring_for_NTTError_from
    def NTTError_from_ExpatError(exc: ExpatError) -> NTTError:  # noqa: N802, D103
        title = "XML"
        summary = "This XML couldn't be parsed"
        src = f"{exc.lineno}:{exc.offset}"
        content = exc.args
        suggestion = "See https://learnxinyminutes.com/xml and https://github.com/martinblech/xmltodict/issues/"
        return NTTError(
            title=title, summary=summary, file=src, content=content, suggestion=suggestion
        )


require_support = mk_require_support(format_name='XML', supported=XML_SUPPORT, extras_name='xml')


def _fix_data(data: TypedData) -> TypedData:
    if (
        isinstance(data, dict)
        and len(data) == 1
        and not isinstance(data[next(iter(data.keys()))], list)  # pyright: ignore [reportArgumentType]
    ):
        return data
    return {'root': data}


@description_more_for_subcommand  # pyright: ignore [reportArgumentType]
@docstring_for_subcommand  # pyright: ignore [reportArgumentType]
class NestedTextToXML(SubcommandOfNestedTextTo):  # noqa: D101
    OTHER_FORMAT = "XML"

    @friendly_exceptions
    @require_support
    def main(self, *NESTED_TEXT_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        self.dump(
            input_files=NESTED_TEXT_FILE,  # pyright: ignore [reportArgumentType]
            dump_stdout=lambda data: xml_unparse(data, output=sys.stdout, pretty=True),  # pyright: ignore [reportPossiblyUnboundVariable, reportCallIssue, reportArgumentType]
            dump_str=lambda data: xml_unparse(data, pretty=True),  # pyright: ignore [reportPossiblyUnboundVariable, reportArgumentType]
            fmt='xml',
            converter=mk_json_types_converter(),
            fix_data=_fix_data,
        )


def _load_file(input_file: LocalPath) -> TypedData:
    try:
        return xml_parse(input_file.open('rb'))  # pyright: ignore [reportPossiblyUnboundVariable]
    except ExpatError as original_e:  # pyright: ignore [reportPossiblyUnboundVariable]
        try:
            input_file.write(f"<root>{input_file.read()}</root>")
            return xml_parse(input_file.open('rb'))  # pyright: ignore [reportPossiblyUnboundVariable]
        except ExpatError:  # pyright: ignore [reportPossiblyUnboundVariable]
            raise original_e from None


def _load_stdin() -> TypedData:
    with local.tempdir() as tmp:
        (tmp / 'input.xml').write(sys.stdin.read())
        return _load_file(tmp / 'input.xml')


@description_more_for_subcommand  # pyright: ignore [reportArgumentType]
@docstring_for_subcommand  # pyright: ignore [reportArgumentType]
class XMLToNestedText(SubcommandOfToNestedText):  # noqa: D101
    OTHER_FORMAT = "XML"

    @friendly_exceptions
    @require_support
    def main(self, *XML_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        self.dump(load_stdin=_load_stdin, load_file=_load_file, input_files=XML_FILE)


SUBCOMMANDS = {
    'nt2': {'names': ('xml',), 'app': NestedTextToXML},
    '2nt': {'names': ('xml',), 'app': XMLToNestedText},
}

EXTENSIONS = ('xml',)
