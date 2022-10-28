"""
CLI definitions, parsing, and entry points.

After argument processing, these call into the `dumpers` functions to get the job done.
"""
import sys

from nestedtext import load as ntload
from plumbum.cli import Application, ExistingFile, Flag, SwitchAttr
from plumbum.colors import blue, green, magenta, yellow
from rich import inspect as _rich_inspect
from rich.console import Console as RichConsole
from ruamel.yaml.parser import ParserError as YAMLParserError
from ruamel.yaml.scanner import ScannerError as YAMLScannerError

from . import __version__
from .dumpers import (
    dump_json_to_nestedtext, dump_json_to_schema, dump_nestedtext_to_json,
    dump_nestedtext_to_toml, dump_nestedtext_to_yaml, dump_toml_to_nestedtext,
    dump_toml_to_schema, dump_yaml_to_nestedtext, dump_yaml_to_schema
)

RICH = RichConsole(stderr=True)


def inspect_exception(exc: Exception):  # pragma: no cover
    """
    Pretty-print an exception to stderr for the user to see.

    Args:
        exc: Any ``Exception``. After printing, it is swallowed, not raised.
    """
    if isinstance(exc, (YAMLParserError, YAMLScannerError)):
        print("This YAML couldn't be parsed", exc, sep='\n', file=sys.stderr)
        return

    _rich_inspect(exc, console=RICH)

    try:
        items = exc.get_codicil()
    except AttributeError:
        pass
    else:
        print(*items, sep='\n', file=sys.stderr)


class _ColorApp(Application):
    PROGNAME = green
    VERSION = __version__ | blue
    COLOR_USAGE = green
    COLOR_GROUPS = {'Meta-switches': magenta, 'Switches': yellow, 'Subcommands': blue}
    ALLOW_ABBREV = True


_ColorApp.unbind_switches('help-all')


class _TypedFormatToSchema(_ColorApp):

    to_schema = Flag(('to-schema', 's'), help="Rather than convert the inputs, generate a schema")


class _NestedTextToTypedFormat(_ColorApp):

    schema_files = SwitchAttr(
        ('schema', 's'),
        argtype=ExistingFile,
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
        nt2json -b '/People/"is a wizard"' -b '/People/"is awake"' example.nt
    """

    def main(self, *input_files: ExistingFile):  # noqa: D102
        try:
            for schema_file in self.schema_files:
                schema = ntload(schema_file)
                self.null_paths = [*schema.get('null', ()), *self.null_paths]
                self.bool_paths = [*schema.get('boolean', ()), *self.bool_paths]
                self.num_paths = [*schema.get('number', ()), *self.num_paths]

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
        nt2yaml -b '/People/"is a wizard"' -b '/People/"is awake"' example.nt
    """

    def main(self, *input_files: ExistingFile):  # noqa: D102
        try:
            for schema_file in self.schema_files:
                schema = ntload(schema_file)
                self.null_paths = [*schema.get('null', ()), *self.null_paths]
                self.bool_paths = [*schema.get('boolean', ()), *self.bool_paths]
                self.num_paths = [*schema.get('number', ()), *self.num_paths]
                self.date_paths = [*schema.get('date', ()), *self.date_paths]

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
        nt2toml -b '/People/"is a wizard"' -b '/People/"is awake"' example.nt
    """

    def main(self, *input_files: ExistingFile):  # noqa: D102
        try:
            for schema_file in self.schema_files:
                schema = ntload(schema_file)
                self.bool_paths = [*schema.get('boolean', ()), *self.bool_paths]
                self.num_paths = [*schema.get('number', ()), *self.num_paths]
                self.date_paths = [*schema.get('date', ()), *self.date_paths]

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

    def main(self, *input_files: ExistingFile):  # noqa: D102
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

    def main(self, *input_files: ExistingFile):  # noqa: D102
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

    def main(self, *input_files: ExistingFile):  # noqa: D102
        try:
            if not self.to_schema:
                dump_toml_to_nestedtext(*input_files)
            else:
                dump_toml_to_schema(*input_files)
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1
