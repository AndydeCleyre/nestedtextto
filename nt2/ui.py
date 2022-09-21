from nestedtext import load as ntload
from plumbum.cli import Application, ExistingFile, SwitchAttr
from plumbum.colors import blue, green, magenta, yellow

from . import __version__
from .internal import (
    dump_json_to_nestedtext, dump_nestedtext_to_json,
    dump_nestedtext_to_yaml, dump_yaml_to_nestedtext
)


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
            "It must be a map with one or more of the keys 'null', 'boolean', 'number',"
            "and each key's value is a list of YAML Paths. TOML and YAML also support 'date'."
        ),
    )
    bool_paths = SwitchAttr(
        ('boolean', 'b'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as boolean",
    )
    null_paths = SwitchAttr(
        ('null', 'n'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as null, if it is an empty string",
    )
    num_paths = SwitchAttr(
        ('number', 'int', 'float', 'i', 'f'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as a number",
    )


class NestedTextToJSON(NestedTextToTypedFormat):
    """
    Read NestedText and output its content as JSON.
    By default, generated JSON values will only contain strings, arrays, and maps,
    but you can cast nodes matching YAML Paths to boolean, null, or number.

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
            num_paths=self.num_paths
        )


class NestedTextToYAML(NestedTextToTypedFormat):
    """
    Read NestedText and output its content as YAML.
    By default, generated YAML values will only contain strings, arrays, and maps,
    but you can cast nodes matching YAML Paths to boolean, null, or number.

    Examples:
        nt2yaml example.nt
        nt2yaml <example.nt
        cat example.nt | nt2yaml
        nt2yaml -b '/People/"is a wizard"' -b '/People/"is awake"' example.nt
    """

    date_paths = SwitchAttr(
        ('date', 'd'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as a date, assuming it's ISO 8601",
    )

    def main(self, *input_files: ExistingFile):
        for schema_file in self.schema_files:
            schema = ntload(schema_file)
            self.null_paths = [*schema.get('null', ()), *self.null_paths]
            self.bool_paths = [*schema.get('boolean', ()), *self.bool_paths]
            self.num_paths = [*schema.get('number', ()), *self.num_paths]
            self.date_paths = [*schema.get('date', ()), *self.date_paths]

        # TODO: YAML date support
        dump_nestedtext_to_yaml(
            *input_files,
            bool_paths=self.bool_paths,
            null_paths=self.null_paths,
            num_paths=self.num_paths,
            date_paths=self.date_paths
        )


class JSONToNestedText(ColorApp):
    """
    Read JSON and output its content as NestedText.

    Examples:
        json2nt example.json
        json2nt <example.json
        cat example.json | json2nt
    """

    # VERSION = __version__
    # SUBCOMMAND_HELPMSG = False

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

    # VERSION = __version__
    # SUBCOMMAND_HELPMSG = False

    def main(self, *input_files: ExistingFile):
        dump_yaml_to_nestedtext(*input_files)
