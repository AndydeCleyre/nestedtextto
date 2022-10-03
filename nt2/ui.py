from nestedtext import load as ntload
from plumbum.cli import Application, ExistingFile, SwitchAttr
from plumbum.colors import blue, green, magenta, yellow

from . import __version__
from .dumpers import (
    dump_json_to_nestedtext, dump_nestedtext_to_json, dump_nestedtext_to_toml,
    dump_nestedtext_to_yaml, dump_toml_to_nestedtext, dump_yaml_to_nestedtext
)

try:
    from rich.traceback import install as rich_tb_install
except ImportError:
    pass
else:
    rich_tb_install()


class ColorApp(Application):
    PROGNAME = green
    VERSION = __version__ | blue
    COLOR_USAGE = green
    COLOR_GROUPS = {'Meta-switches': magenta, 'Switches': yellow, 'Subcommands': blue}
    ALLOW_ABBREV = True


ColorApp.unbind_switches('help-all')


class NestedTextToTypedFormat(ColorApp):

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


class NestedTextToTypedFormatSupportNull(ColorApp):

    null_paths = SwitchAttr(
        ('null', 'n'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as null, if it is an empty string",
    )


class NestedTextToTypedFormatSupportDate(ColorApp):

    date_paths = SwitchAttr(
        ('date', 'd'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as a date, assuming it's ISO 8601",
    )


class NestedTextToJSON(NestedTextToTypedFormat, NestedTextToTypedFormatSupportNull):
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

    def main(self, *input_files: ExistingFile):
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


class NestedTextToYAML(
    NestedTextToTypedFormat, NestedTextToTypedFormatSupportNull, NestedTextToTypedFormatSupportDate
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

    def main(self, *input_files: ExistingFile):
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


class NestedTextToTOML(NestedTextToTypedFormat, NestedTextToTypedFormatSupportDate):
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

    def main(self, *input_files: ExistingFile):
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


class JSONToNestedText(ColorApp):
    """
    Read JSON and output its content as NestedText.

    Examples:
        json2nt example.json
        json2nt <example.json
        cat example.json | json2nt
    """

    # --make-schema ? --gen-schema ? --only-schema ? separate command?

    def main(self, *input_files: ExistingFile):
        dump_json_to_nestedtext(*input_files)


class YAMLToNestedText(ColorApp):
    """
    Read YAML and output its content as NestedText.

    Examples:
        yaml2nt example.yml
        yaml2nt <example.yml
        cat example.yml | yaml2nt
    """

    def main(self, *input_files: ExistingFile):
        dump_yaml_to_nestedtext(*input_files)


class TOMLToNestedText(ColorApp):
    """
    Read TOML and output its content as NestedText.

    Examples:
        toml2nt example.yml
        toml2nt <example.yml
        cat example.yml | toml2nt
    """

    def main(self, *input_files: ExistingFile):
        dump_toml_to_nestedtext(*input_files)
