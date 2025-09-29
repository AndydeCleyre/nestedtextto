"""
CLI definitions, parsing, and entry points.

After argument processing, these call into the `dumpers` functions to get the job done.
"""

import sys
from json import JSONDecodeError
from typing import ClassVar, cast

from nestedtext import NestedTextError, load as ntload
from plumbum import local
from plumbum.cli import Application, ExistingFile, Flag, Range, Set, SwitchAttr
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
    dump_huml_to_nestedtext,
    dump_huml_to_schema,
    dump_json_to_nestedtext,
    dump_json_to_schema,
    dump_nestedtext_to_huml,
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


class _ColorSubcommand(_ColorApp):
    ALLOW_ABBREV = True


_ColorSubcommand.unbind_switches('help-all')


class _TypedFormatToSchema(_ColorSubcommand):
    to_schema = Flag(('to-schema', 's'), help="Rather than convert the inputs, generate a schema")


class _ToNestedText(_TypedFormatToSchema):
    inline_width = SwitchAttr(
        ('inline-width', 'i'),
        argtype=Range(0, 120),  # type: ignore
        default=0,
        argname='WIDTH',
        help="Maximum line width for inline dictionaries and lists",
    )


class _NestedTextToTypedFormat(_ColorSubcommand):
    schema_files = SwitchAttr(
        ('schema', 's'),
        argtype=ExistingFile,  # type: ignore
        list=True,
        argname='NESTED_TEXT_FILE',
        help=(
            "Cast nodes matching YAML Path queries specified in a NestedText document. "
            "It must be a map with one or more of the keys: 'null', 'boolean', 'number'. "
            "Each key's value is a list of YAML Paths"
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


class _NestedTextToTypedFormatSupportNull(_ColorSubcommand):
    null_paths = SwitchAttr(
        ('null', 'n'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as null, if it is an empty string",
    )


class _NestedTextToTypedFormatSupportDate(_ColorSubcommand):
    date_paths = SwitchAttr(
        ('date', 'd'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as a date, assuming it's ISO 8601",
    )


class NestedTextTo(_ColorApp):
    """Convert NestedText to another format."""


@NestedTextTo.subcommand('completion')  # pyright: ignore [reportCallIssue]
class PrintShellCompletion(_ColorSubcommand):
    """Print completion code for the given shell."""

    DESCRIPTION_MORE = """
Examples:

  - nt2 completion zsh >~/.local/share/zsh/site-functions/_nt2
  - nt2 completion bash >~/.local/share/bash-completion/completions/nt2
  - nt2 completion fish >~/.config/fish/completions/nt2.fish
"""

    def main(self, SHELL: Set('zsh', 'bash', 'fish')):  # type: ignore  # noqa: D102,N803
        data_dir = local.path(__file__).up(2) / 'data'
        if not data_dir.exists():
            data_dir = local.path(__file__).up(5)

        bread_crumbs = {
            'zsh': ('share', 'zsh', 'site-functions', '_nt2'),
            'bash': ('share', 'bash-completion', 'completions', 'nt2'),
            'fish': ('config', 'fish', 'completions', 'nt2.fish'),
        }[SHELL]

        comp_file = data_dir.join(*bread_crumbs)

        if comp_file.exists():
            print(comp_file.read())
        else:
            print(
                f"{comp_file} not found.\n"
                "Report @ https://github.com/AndydeCleyre/nestedtextto/issues\n"
                "Find the file @ https://github.com/AndydeCleyre/nestedtextto/tree/master/data",
                file=sys.stderr,
            )
            sys.exit(1)


NT2_DESCRIPTION_MORE_TMPL = """
By default, generated {target} values will only contain strings, arrays, and maps,
but you can cast nodes matching YAML Paths to {types}.

Casting switches may be before or after file arguments.

Examples:

    - nt2 {subcommand} config.nt >config.{extension}
    - cat config.nt | nt2 {subcommand}
    - nt2 {subcommand} --schema config.types.nt config.nt >config.{extension}
    - nt2 {subcommand} --int stats.total --boolean config.enabled data.nt
"""


class ToNestedText(_ColorApp):
    """Convert another format to NestedText."""


@NestedTextTo.subcommand('json')  # pyright: ignore [reportCallIssue]
class NestedTextToJSON(_NestedTextToTypedFormat, _NestedTextToTypedFormatSupportNull):
    """Read NestedText and output its content as JSON."""

    DESCRIPTION_MORE = NT2_DESCRIPTION_MORE_TMPL.format(
        target="JSON", types="boolean, null, or number", subcommand="json", extension="json"
    )
    DESCRIPTION_MORE += (
        "\nIt can be invoked as either the subcommand `nt2 json`"
        " or the single command `nt2json`.\n"
    )

    def main(self, *NESTED_TEXT_FILE: ExistingFile):  # type: ignore  # noqa: D102,ANN201,N803
        try:
            for schema_file in cast(list, self.schema_files):
                schema = cast(dict, ntload(schema_file))
                self.null_paths = [*schema.get('null', ()), *cast(list, self.null_paths)]
                self.bool_paths = [*schema.get('boolean', ()), *cast(list, self.bool_paths)]
                self.num_paths = [*schema.get('number', ()), *cast(list, self.num_paths)]

            dump_nestedtext_to_json(
                *NESTED_TEXT_FILE,
                bool_paths=self.bool_paths,
                null_paths=self.null_paths,
                num_paths=self.num_paths,
            )
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1


@NestedTextTo.subcommand('yaml')  # pyright: ignore [reportCallIssue]
class NestedTextToYAML(
    _NestedTextToTypedFormat,
    _NestedTextToTypedFormatSupportNull,
    _NestedTextToTypedFormatSupportDate,
):
    """Read NestedText and output its content as YAML."""

    DESCRIPTION_MORE = NT2_DESCRIPTION_MORE_TMPL.format(
        target="YAML", types="boolean, null, number, or date", subcommand="yaml", extension="yml"
    )
    DESCRIPTION_MORE += (
        "\nIt can be invoked as either the subcommand `nt2 yaml`"
        " or the single command `nt2yaml`.\n"
    )

    def main(self, *NESTED_TEXT_FILE: ExistingFile):  # type: ignore  # noqa: D102,ANN201,N803
        try:
            for schema_file in cast(list, self.schema_files):
                schema = cast(dict, ntload(schema_file))
                self.null_paths = [*schema.get('null', ()), *cast(list, self.null_paths)]
                self.bool_paths = [*schema.get('boolean', ()), *cast(list, self.bool_paths)]
                self.num_paths = [*schema.get('number', ()), *cast(list, self.num_paths)]
                self.date_paths = [*schema.get('date', ()), *cast(list, self.date_paths)]

            dump_nestedtext_to_yaml(
                *NESTED_TEXT_FILE,
                bool_paths=self.bool_paths,
                null_paths=self.null_paths,
                num_paths=self.num_paths,
                date_paths=self.date_paths,
            )
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1


@NestedTextTo.subcommand('toml')  # pyright: ignore [reportCallIssue]
class NestedTextToTOML(_NestedTextToTypedFormat, _NestedTextToTypedFormatSupportDate):
    """Read NestedText and output its content as TOML."""

    DESCRIPTION_MORE = NT2_DESCRIPTION_MORE_TMPL.format(
        target="TOML", types="boolean, number, or date", subcommand="toml", extension="toml"
    )
    DESCRIPTION_MORE += (
        "\nIt can be invoked as either the subcommand `nt2 toml`"
        " or the single command `nt2toml`.\n"
    )

    def main(self, *NESTED_TEXT_FILE: ExistingFile):  # type: ignore  # noqa: D102,ANN201,N803
        try:
            for schema_file in cast(list, self.schema_files):
                schema = cast(dict, ntload(schema_file))
                self.bool_paths = [*schema.get('boolean', ()), *cast(list, self.bool_paths)]
                self.num_paths = [*schema.get('number', ()), *cast(list, self.num_paths)]
                self.date_paths = [*schema.get('date', ()), *cast(list, self.date_paths)]

            dump_nestedtext_to_toml(
                *NESTED_TEXT_FILE,
                bool_paths=self.bool_paths,
                num_paths=self.num_paths,
                date_paths=self.date_paths,
            )
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1


@NestedTextTo.subcommand('huml')  # pyright: ignore [reportCallIssue]
class NestedTextToHUML(_NestedTextToTypedFormat, _NestedTextToTypedFormatSupportNull):
    """Read NestedText and output its content as HUML."""

    DESCRIPTION_MORE = NT2_DESCRIPTION_MORE_TMPL.format(
        target="HUML", types="boolean, null, or number", subcommand="huml", extension="huml"
    )

    def main(self, *NESTED_TEXT_FILE: ExistingFile):  # type: ignore  # noqa: D102,ANN201,N803
        try:
            for schema_file in cast(list, self.schema_files):
                schema = cast(dict, ntload(schema_file))
                self.null_paths = [*schema.get('null', ()), *cast(list, self.null_paths)]
                self.bool_paths = [*schema.get('boolean', ()), *cast(list, self.bool_paths)]
                self.num_paths = [*schema.get('number', ()), *cast(list, self.num_paths)]

            dump_nestedtext_to_huml(
                *NESTED_TEXT_FILE,
                bool_paths=self.bool_paths,
                null_paths=self.null_paths,
                num_paths=self.num_paths,
            )
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1


@ToNestedText.subcommand('json')  # pyright: ignore [reportCallIssue]
class JSONToNestedText(_ToNestedText):
    """Read JSON and output its content as NestedText."""

    DESCRIPTION_MORE = """
Examples:

    - 2nt json data.json >data.nt
    - curl -s https://api.example.com/data | 2nt json
    - 2nt json --to-schema data.json >data.types.nt

It can be invoked as either the subcommand `2nt json` or the single command `json2nt`.
"""

    def main(self, *JSON_FILE: ExistingFile):  # type: ignore  # noqa: D102,ANN201,N803
        try:
            if not self.to_schema:
                dump_json_to_nestedtext(*JSON_FILE, inline_width=cast(int, self.inline_width))
            else:
                dump_json_to_schema(*JSON_FILE)
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1


@ToNestedText.subcommand('yaml')  # pyright: ignore [reportCallIssue]
class YAMLToNestedText(_ToNestedText):
    """Read YAML and output its content as NestedText."""

    DESCRIPTION_MORE = """
Examples:

    - 2nt yaml config.yml >config.nt
    - kubectl get deployment -o yaml | 2nt yaml
    - 2nt yaml --to-schema config.yml >config.types.nt

It can be invoked as either the subcommand `2nt yaml` or the single command `yaml2nt`.
"""

    def main(self, *YAML_FILE: ExistingFile):  # type: ignore  # noqa: D102,ANN201,N803
        try:
            if not self.to_schema:
                dump_yaml_to_nestedtext(*YAML_FILE, inline_width=cast(int, self.inline_width))
            else:
                dump_yaml_to_schema(*YAML_FILE)
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1


@ToNestedText.subcommand('toml')  # pyright: ignore [reportCallIssue]
class TOMLToNestedText(_ToNestedText):
    """Read TOML and output its content as NestedText."""

    DESCRIPTION_MORE = """
Examples:

    - 2nt toml config.toml >config.nt
    - cat config.toml | 2nt toml
    - 2nt toml --to-schema config.toml >config.types.nt

It can be invoked as either the subcommand `2nt toml` or the single command `toml2nt`.
"""

    def main(self, *TOML_FILE: ExistingFile):  # type: ignore  # noqa: D102,ANN201,N803
        try:
            if not self.to_schema:
                dump_toml_to_nestedtext(*TOML_FILE, inline_width=cast(int, self.inline_width))
            else:
                dump_toml_to_schema(*TOML_FILE)
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1


@ToNestedText.subcommand('huml')  # pyright: ignore [reportCallIssue]
class HUMLToNestedText(_ToNestedText):
    """Read HUML and output its content as NestedText."""

    DESCRIPTION_MORE = """
Examples:

    - 2nt huml config.huml >config.nt
    - cat config.huml | 2nt huml
    - 2nt huml --to-schema config.huml >config.types.nt
"""

    def main(self, *HUML_FILE: ExistingFile):  # type: ignore  # noqa: D102,ANN201,N803
        try:
            if not self.to_schema:
                dump_huml_to_nestedtext(*HUML_FILE, inline_width=cast(int, self.inline_width))
            else:
                dump_huml_to_schema(*HUML_FILE)
        except Exception as e:  # pragma: no cover
            inspect_exception(e)
            return 1
