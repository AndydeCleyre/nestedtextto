"""Support for YAML."""

from __future__ import annotations

import io
import sys
from typing import TYPE_CHECKING

from plumbum import local
from plumbum.cli import ExistingFile  # noqa: TC002

from nt2.commands import (
    SubcommandOfNestedTextTo,
    SubcommandOfToNestedText,
    SupportsDate,
    SupportsNull,
    SupportsTypes,
    description_more_for_subcommand,
    docstring_for_subcommand,
)
from nt2.converters import mk_yaml_types_converter
from nt2.exceptions import (
    NTTError,
    NTTError_from,
    docstring_for_NTTError_from,
    friendly_exceptions,
)

if TYPE_CHECKING:
    from plumbum import LocalPath

    from nt2.types import YAMLData
from ruamel.yaml.error import MarkedYAMLError  # noqa: TC002
from ruamel.yaml.scalarstring import walk_tree as use_multiline_syntax

from nt2.yamlpath_tools import mk_yaml_editor

YAML_EDITOR = mk_yaml_editor()


@NTTError_from.register
@docstring_for_NTTError_from
def NTTError_from_MarkedYAMLError(exc: MarkedYAMLError) -> NTTError:  # noqa: N802, D103
    title = "YAML"
    summary = "This YAML couldn't be parsed"
    content = tuple(m for m in (exc.context, exc.problem, exc.note) if m)
    if content:
        content = (content[0].capitalize(), *content[1:])
    src = exc.problem_mark and exc.problem_mark.name
    if src and src != '<stdin>':
        src_file = local.path(src)
        if src_file.exists():
            src = src_file.relative_to(local.cwd)
    # line + 1 ?
    src = ':'.join(
        str(m)
        for m in (
            src,
            exc.problem_mark and exc.problem_mark.line,
            exc.problem_mark and exc.problem_mark.column,
        )
        if m
    )
    # What good is context_mark?
    suggestion = "See https://learnxinyminutes.com/yaml"
    return NTTError(title=title, summary=summary, file=src, content=content, suggestion=suggestion)


def _dump_str(data: YAMLData) -> str:
    """
    Return the data a a YAML string, without color.

    Args:
        data: The YAML data.

    Returns:
        The YAML string.

    Raises:
        Exception: If there was an error.
    """
    use_multiline_syntax(data)
    out_stream = io.StringIO()
    try:
        YAML_EDITOR.dump(data, out_stream)
    except Exception:
        raise
    else:
        return out_stream.getvalue()
    finally:
        out_stream.close()


def _dump_stdout(data: YAMLData):
    """
    Print the data a a YAML string, without color.

    Args:
        data: The YAML data.
    """
    use_multiline_syntax(data)
    YAML_EDITOR.dump(data, sys.stdout)


def _load_file(input_file: LocalPath) -> YAMLData:
    """
    Read YAML from input_file and return typed data.

    Args:
        input_file: The YAML file.

    Returns:
        The YAML data.
    """
    with input_file.open(encoding='utf-8') as ifile:
        return YAML_EDITOR.load(ifile)


@description_more_for_subcommand  # pyright: ignore [reportArgumentType]
@docstring_for_subcommand  # pyright: ignore [reportArgumentType]
class NestedTextToYAML(SupportsTypes, SupportsNull, SupportsDate, SubcommandOfNestedTextTo):  # noqa: D101
    OTHER_FORMAT = "YAML"

    @friendly_exceptions
    def main(self, *NESTED_TEXT_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        self.dump(
            input_files=NESTED_TEXT_FILE,  # pyright: ignore [reportArgumentType]
            dump_stdout=_dump_stdout,  # pyright: ignore [reportArgumentType]
            dump_str=_dump_str,  # pyright: ignore [reportArgumentType]
            fmt='yml',
            converter=mk_yaml_types_converter(),
        )


@description_more_for_subcommand  # pyright: ignore [reportArgumentType]
@docstring_for_subcommand  # pyright: ignore [reportArgumentType]
class YAMLToNestedText(SubcommandOfToNestedText):  # noqa: D101
    OTHER_FORMAT = "YAML"

    @friendly_exceptions
    def main(self, *YAML_FILE: ExistingFile) -> int | None:  # type: ignore  # noqa: D102,N803
        self.dump(
            load_stdin=lambda: YAML_EDITOR.load(sys.stdin),
            load_file=_load_file,
            input_files=YAML_FILE,
        )


# TODO: Add 'yml' to names:
#   https://github.com/tomerfiliba/plumbum/issues/717
SUBCOMMANDS = {
    'nt2': {'app': NestedTextToYAML, 'names': ('yaml',)},
    '2nt': {'app': YAMLToNestedText, 'names': ('yaml',)},
}

EXTENSIONS = ('yml', 'yaml')
