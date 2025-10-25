"""
CLI definitions, parsing, and entry points.

After argument processing, these call into the `dumpers` functions to get the job done.
"""

from __future__ import annotations

import sys
from importlib import import_module, resources
from typing import TYPE_CHECKING, cast

from plumbum import local
from plumbum.cli import ExistingFile, Set, SwitchAttr

from .commands import (
    Command,
    Subcommand,
    SubcommandOfToNestedText,
    SupportsTypes,
    ToNestedTextBase,
    get_ntt_stdout,
    invoke_ntt_command,
    propagate_options_to_subcommand,
)
from .exceptions import NTTError, friendly_exceptions

if TYPE_CHECKING:
    from plumbum import LocalPath

FORMATS = [
    import_module(f"nt2.formats.{fmt.split('.', 1)[0]}")
    for fmt in resources.contents('nt2.formats')
    if (fmt not in 'nestedtext.py' and not fmt.startswith('__'))
]

SUBCOMMANDS_2NT, SUBCOMMANDS_NT2, SUBCOMMANDS_NT2_NAMES = {}, {}, set()
for fmt in FORMATS:
    SUBCOMMANDS_NT2_NAMES.update(fmt.SUBCOMMANDS['nt2']['names'])
    for ext in fmt.EXTENSIONS:
        SUBCOMMANDS_2NT[ext] = fmt.SUBCOMMANDS['2nt']['app']
        SUBCOMMANDS_NT2[ext] = fmt.SUBCOMMANDS['nt2']['app']
SUBCOMMANDS_NT2_NAMES = sorted(SUBCOMMANDS_NT2_NAMES)


class WithFromSwitch:
    """Mixin for adding the -f/--from switch."""

    from_format = SwitchAttr(
        ('from', 'f'),
        argtype=Set(*SUBCOMMANDS_2NT.keys(), case_sensitive=False),  # pyright: ignore [reportArgumentType]
        argname='FROM_FORMAT',
        help="Format to convert from",
    )


def _determine_2nt_subcommand(
    from_format: str | None, data_file: LocalPath | None = None
) -> SubcommandOfToNestedText:
    """
    Return the appropriate 2nt subcommand for the input file and from_format switch value.

    Args:
        from_format: The -f/--from switch value.
        data_file: The input file to determine the 2nt subcommand for.

    Returns:
        The appropriate 2nt subcommand for the input file and -f/--from switch value.

    Raises:
        NTTError: If the subcommand cannot be determined.
    """
    subcommand = (from_format and SUBCOMMANDS_2NT.get(from_format)) or (
        data_file and SUBCOMMANDS_2NT.get(data_file.suffix.lower().lstrip('.'))
    )

    if not subcommand:
        raise NTTError(
            title="Unknown input format",
            file=str(data_file or "<stdin>"),
            suggestion=(
                "Specify the input format with -f/--from, e.g. '-f json', "
                "or use a subcommand, such as 'json', 'toml', or 'yaml'"
            ),
            summary="No format autodetection for stdin, sorry!" if not data_file else None,
        )

    return cast('SubcommandOfToNestedText', subcommand)


class ToNestedText(ToNestedTextBase, WithFromSwitch):
    """Convert another format to NestedText."""

    DESCRIPTION_MORE = """
Examples:
    - 2nt config.json
    - 2nt config.json --to-schema >config.types.nt
    - cat config.json | 2nt json
    - cat config.json | 2nt --from json
"""

    @friendly_exceptions  # pyright: ignore [reportCallIssue]
    def main(self, *DATA_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        if self.nested_command:
            propagate_options_to_subcommand(self, ('inline-width', 'to-schema'))
            return None

        # TODO: https://github.com/tomerfiliba/plumbum/issues/716
        propagated_kwargs = {'inline_width': self.inline_width}
        if self.to_schema:
            propagated_kwargs['to_schema'] = self.to_schema

        error_kwargs = {
            'title': "Error converting to NestedText",
            'suggestion': (
                "Confirm the input format, and specify it with -f/--from, e.g. '-f json', "
                "or use a subcommand, such as 'json', 'toml', or 'yaml'"
            ),
        }

        if not DATA_FILE and not sys.stdin.isatty():
            subcommand = _determine_2nt_subcommand(cast(str | None, self.from_format))
            invoke_ntt_command(subcommand, error_kwargs, **propagated_kwargs)
            return
        for data_file in DATA_FILE:
            subcommand = _determine_2nt_subcommand(cast(str | None, self.from_format), data_file)
            error_kwargs['file'] = str(data_file)
            invoke_ntt_command(subcommand, error_kwargs, data_file, **propagated_kwargs)


class NestedTextTo(Command):
    """Convert NestedText to another format."""

    DESCRIPTION_MORE = """
Examples:
    - nt2 json config.nt
    - nt2 json config.nt --number font.size --boolean font.bold
    - nt2 json config.nt --schema config.types.nt
    - cat config.nt | nt2 json
"""


for fmt in FORMATS:
    for name in fmt.SUBCOMMANDS['nt2']['names']:
        NestedTextTo.subcommand(name, fmt.SUBCOMMANDS['nt2']['app'])
    for name in fmt.SUBCOMMANDS['2nt']['names']:
        ToNestedText.subcommand(name, fmt.SUBCOMMANDS['2nt']['app'])


def _to_nested_text_to_with_stdin_as_file(from_format: str | None, to_format: str):
    # raises NTTError if from_format not set and valid:
    _determine_2nt_subcommand(from_format)

    input_content = sys.stdin.read()
    with local.tempdir() as tmpdir:
        input_file = tmpdir / f"input.{from_format}"
        input_file.write(input_content)

        invoke_ntt_command(
            cast('Command', ToNestedTextTo),
            {'title': "Error converting to, then from, NestedText", 'file': "<stdin>"},
            to_format,
            input_file,
            from_format=from_format,
        )


class ToNestedTextTo(Command, WithFromSwitch):
    """Convert another format to another format, by way of NestedText."""

    DESCRIPTION_MORE = """
Examples:
    - 2nt2 json pyproject.toml
    - cat pyproject.toml | 2nt2 json --from toml
"""

    # TODO: the generated USAGE is not good enough,
    #         make a plumbum issue to follow this
    USAGE = (
        "    2nt2 [SWITCHES] TO_FORMAT:{{" + ', '.join(SUBCOMMANDS_NT2_NAMES) + "}} DATA_FILE...\n"
    )

    @friendly_exceptions  # pyright: ignore [reportCallIssue]
    def main(  # type: ignore  # noqa: D102
        self,
        TO_FORMAT: Set(*SUBCOMMANDS_NT2_NAMES, case_sensitive=False),  # type: ignore  # noqa: N803
        *DATA_FILE: ExistingFile,  # type: ignore  # noqa: N803
    ) -> int | None:
        if not DATA_FILE and not sys.stdin.isatty():
            _to_nested_text_to_with_stdin_as_file(cast(str | None, self.from_format), TO_FORMAT)
            return

        subcommand_nt2 = SUBCOMMANDS_NT2[TO_FORMAT]
        provide_schema = issubclass(subcommand_nt2, SupportsTypes)

        for data_file in DATA_FILE:
            subcommand_2nt = _determine_2nt_subcommand(
                cast(str | None, self.from_format), data_file
            )
            nt_content = get_ntt_stdout(
                subcommand_2nt,
                {
                    'title': "Error converting to NestedText",
                    'file': str(data_file),
                    'suggestion': (
                        "Confirm the input format, and specify it with -f/--from, e.g. '-f json'"
                    ),
                },
                data_file,
            )
            if provide_schema:
                schema_content = get_ntt_stdout(
                    subcommand_2nt,
                    {
                        'title': "Error generating NestedText schema",
                        'file': str(data_file),
                        'suggestion': "Report a bug at https://github.com/AndydeCleyre/NestedTextTo/issues",
                    },
                    data_file,
                    to_schema=True,
                )

            with local.tempdir() as tmpdir:
                nt_file = tmpdir / 'data.nt'
                nt_file.write(nt_content)

                nt2_kwargs = {}
                if provide_schema:
                    schema_file = tmpdir / 'schema.nt'
                    schema_file.write(schema_content)  # pyright: ignore [reportPossiblyUnboundVariable]
                    nt2_kwargs['schema_files'] = [schema_file]

                invoke_ntt_command(
                    subcommand_nt2,
                    {
                        'title': "Error converting from NestedText",
                        'suggestion': "Report a bug at https://github.com/AndydeCleyre/NestedTextTo/issues",
                    },
                    nt_file,
                    **nt2_kwargs,
                )


ToNestedTextTo.unbind_switches('help-all')


@ToNestedText.subcommand('completion')  # pyright: ignore [reportCallIssue]
@NestedTextTo.subcommand('completion')  # pyright: ignore [reportCallIssue]
class PrintShellCompletion(Subcommand):
    """Print completion code for the given shell."""

    DESCRIPTION_MORE = """
Examples:
  - nt2 completion zsh >~/.local/share/zsh/site-functions/_nt2
  - nt2 completion bash >~/.local/share/bash-completion/completions/nt2
  - nt2 completion fish >~/.config/fish/completions/nt2.fish
"""

    @friendly_exceptions  # pyright: ignore [reportCallIssue]
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
            raise NTTError(
                title=f"{comp_file} not found.",
                summary="Find the file at https://github.com/AndydeCleyre/nestedtextto/tree/master/data",
                suggestion="Report a bug at https://github.com/AndydeCleyre/NestedTextTo/issues",
            )
