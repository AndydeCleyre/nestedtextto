"""
CLI definitions, parsing, and entry points.

After argument processing, these call into the `dumpers` functions to get the job done.
"""

import sys
from json import JSONDecodeError
from typing import ClassVar, cast

from nestedtext import NestedTextError, load as ntload
from plumbum.cli import Application, ExistingFile, Flag, SwitchAttr
from plumbum.colors import (
    blue,  # pyright: ignore [reportAttributeAccessIssue]
    green,  # pyright: ignore [reportAttributeAccessIssue]
    magenta,  # pyright: ignore [reportAttributeAccessIssue]
    yellow,  # pyright: ignore [reportAttributeAccessIssue]
)
from rich import inspect as _rich_inspect
from rich.console import Console as RichConsole
from ruamel.yaml.parser import ParserError as YAMLParserError
from ruamel.yaml.scanner import ScannerError as YAMLScannerError

from . import __version__
from .dumpers import (
    dump_json_to_nestedtext,
    dump_json_to_schema,
    dump_nestedtext_to_json,
    dump_nestedtext_to_toml,
    dump_nestedtext_to_yaml,
    dump_toml_to_nestedtext,
    dump_toml_to_schema,
    dump_yaml_to_nestedtext,
    dump_yaml_to_schema,
)

RICH = RichConsole(stderr=True)


def inspect_exception(exc: Exception):  # pragma: no cover
    """
    Pretty-print an exception to stderr for the user to see.

    Args:
        exc: Any ``Exception``. After printing, it is swallowed, not raised.
    """
    _rich_inspect(exc, console=RICH, value=False)

    if isinstance(exc, (YAMLParserError, YAMLScannerError)):
        print("This YAML couldn't be parsed", exc, sep='\n', file=sys.stderr)
        return

    if isinstance(exc, JSONDecodeError):
        lines = exc.doc.splitlines()
        print(
            "This JSON couldn't be parsed",
            exc,
            *lines[max(0, exc.lineno - 3) : exc.lineno],
            f"{'.' * (exc.colno - 1)}▲" | magenta,
            *lines[exc.lineno : exc.lineno + 2],
            sep='\n',
            file=sys.stderr,
        )
        return

    if isinstance(exc, NestedTextError):
        print(*filter(None, exc.get_codicil()), sep='\n', file=sys.stderr)


class _ColorApp(Application):
    PROGNAME = green
    VERSION = __version__ | blue
    COLOR_USAGE = green
    COLOR_GROUPS: ClassVar = {'Meta-switches': magenta, 'Switches': yellow, 'Subcommands': blue}
    ALLOW_ABBREV = True


_ColorApp.unbind_switches('help-all')


class _TypedFormatToSchema(_ColorApp):
    to_schema = Flag(('to-schema', 's'), help="Rather than convert the inputs, generate a schema")


class _NestedTextToTypedFormat(_ColorApp):
    schema_files = SwitchAttr(
        ('schema', 's'),
        argtype=ExistingFile,  # type: ignore
        list=True,
        argname='NESTEDTEXTFILE',
        help=(
            "Cast nodes matching YAML Path queries specified in a NestedText document. "
            "It must be a map with one or more of the keys: 'null', 'boolean', 'number'"
            "Each key's value is a list of YAML Paths."
        ),
    )
    bool_paths = SwitchAttr(
        ('boolean', 'b'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as boolean",
    )
    num_paths = SwitchAttr(
        ('number', 'int', 'float', 'i', 'f'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as a number",
    )


class _NestedTextToTypedFormatSupportNull(_ColorApp):
    null_paths = SwitchAttr(
        ('null', 'n'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as null, if it is an empty string",
    )


class _NestedTextToTypedFormatSupportDate(_ColorApp):
    date_paths = SwitchAttr(
        ('date', 'd'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as a date, assuming it's ISO 8601",
    )


class NestedTextToJSON(_NestedTextToTypedFormat, _NestedTextToTypedFormatSupportNull):
    """
    Read NestedText and output its content as JSON.

    By default, generated JSON values will only contain strings, arrays, and maps,
    but you can cast nodes matching YAML Paths to boolean, null, or number.

    Casting switches may be before or after file arguments.

    Examples:
        nt2json example.nt
        nt2json <example.nt
        cat example.nt | nt2json
        nt2json --int People.age --boolean 'People."is a wizard"' example.nt
    """

    def main(self, *input_files: ExistingFile):  # type: ignore  # noqa: D102,ANN201
        try:
            for schema_file in cast(list, self.schema_files):
                schema = cast(dict, ntload(schema_file))
                self.null_paths = [*schema.get('null', ()), *cast(list, self.null_paths)]
                self.bool_paths = [*schema.get('boolean', ()), *cast(list, self.bool_paths)]
                self.num_paths = [*schema.get('number', ()), *cast(list, self.num_paths)]

            dump_nestedtext_to_json(
                *input_files,
                bool_paths=self.bool_paths,
                null_paths=self.null_paths,
                num_paths=self.num_paths,
            )
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1


class NestedTextToYAML(
    _NestedTextToTypedFormat,
    _NestedTextToTypedFormatSupportNull,
    _NestedTextToTypedFormatSupportDate,
):
    """
    Read NestedText and output its content as YAML.

    By default, generated YAML values will only contain strings, arrays, and maps,
    but you can cast nodes matching YAML Paths to boolean, null, number, or date.

    Casting switches may be before or after file arguments.

    Examples:
        nt2yaml example.nt
        nt2yaml <example.nt
        cat example.nt | nt2yaml
        nt2yaml --int People.age --boolean 'People."is a wizard"' example.nt
    """

    def main(self, *input_files: ExistingFile):  # type: ignore  # noqa: D102,ANN201
        try:
            for schema_file in cast(list, self.schema_files):
                schema = cast(dict, ntload(schema_file))
                self.null_paths = [*schema.get('null', ()), *cast(list, self.null_paths)]
                self.bool_paths = [*schema.get('boolean', ()), *cast(list, self.bool_paths)]
                self.num_paths = [*schema.get('number', ()), *cast(list, self.num_paths)]
                self.date_paths = [*schema.get('date', ()), *cast(list, self.date_paths)]

            dump_nestedtext_to_yaml(
                *input_files,
                bool_paths=self.bool_paths,
                null_paths=self.null_paths,
                num_paths=self.num_paths,
                date_paths=self.date_paths,
            )
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1


class NestedTextToTOML(_NestedTextToTypedFormat, _NestedTextToTypedFormatSupportDate):
    """
    Read NestedText and output its content as TOML.

    By default, generated TOML values will only contain strings, arrays, and maps,
    but you can cast nodes matching YAML Paths to boolean, number, or date.

    Casting switches may be before or after file arguments.

    Examples:
        nt2toml example.nt
        nt2toml <example.nt
        cat example.nt | nt2toml
        nt2toml --int People.age --boolean 'People."is a wizard"' example.nt
    """

    def main(self, *input_files: ExistingFile):  # type: ignore  # noqa: D102,ANN201
        try:
            for schema_file in cast(list, self.schema_files):
                schema = cast(dict, ntload(schema_file))
                self.bool_paths = [*schema.get('boolean', ()), *cast(list, self.bool_paths)]
                self.num_paths = [*schema.get('number', ()), *cast(list, self.num_paths)]
                self.date_paths = [*schema.get('date', ()), *cast(list, self.date_paths)]

            dump_nestedtext_to_toml(
                *input_files,
                bool_paths=self.bool_paths,
                num_paths=self.num_paths,
                date_paths=self.date_paths,
            )
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1


class JSONToNestedText(_TypedFormatToSchema):
    """
    Read JSON and output its content as NestedText.

    Examples:
        json2nt example.json
        json2nt <example.json
        cat example.json | json2nt
    """

    def main(self, *input_files: ExistingFile):  # type: ignore  # noqa: D102,ANN201
        try:
            if not self.to_schema:
                dump_json_to_nestedtext(*input_files)
            else:
                dump_json_to_schema(*input_files)
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1


class YAMLToNestedText(_TypedFormatToSchema):
    """
    Read YAML and output its content as NestedText.

    Examples:
        yaml2nt example.yml
        yaml2nt <example.yml
        cat example.yml | yaml2nt
    """

    def main(self, *input_files: ExistingFile):  # type: ignore  # noqa: D102,ANN201
        try:
            if not self.to_schema:
                dump_yaml_to_nestedtext(*input_files)
            else:
                dump_yaml_to_schema(*input_files)
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1


class TOMLToNestedText(_TypedFormatToSchema):
    """
    Read TOML and output its content as NestedText.

    Examples:
        toml2nt example.yml
        toml2nt <example.yml
        cat example.yml | toml2nt
    """

    def main(self, *input_files: ExistingFile):  # type: ignore  # noqa: D102,ANN201
        try:
            if not self.to_schema:
                dump_toml_to_nestedtext(*input_files)
            else:
                dump_toml_to_schema(*input_files)
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1
