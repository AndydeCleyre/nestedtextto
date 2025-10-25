"""Shared CLI objects, used by .ui and .formats."""

from __future__ import annotations

import io
import sys
from typing import TYPE_CHECKING, ClassVar, cast

if TYPE_CHECKING:
    from typing import Any, Callable, Sequence, Type

    from cattrs import Converter
    from plumbum import LocalPath

    from .types import Schema, TypedData

from plumbum.cli import Application, ExistingFile, Flag, Range, SwitchAttr
from plumbum.colors import (
    blue,  # pyright: ignore [reportAttributeAccessIssue]
    green,  # pyright: ignore [reportAttributeAccessIssue]
    magenta,  # pyright: ignore [reportAttributeAccessIssue]
    yellow,  # pyright: ignore [reportAttributeAccessIssue]
)

from . import __version__
from .dumpers import dump_from_nestedtext, dump_to_nestedtext, dump_to_schema
from .exceptions import NTTError
from .formats import nestedtext


class Command(Application):
    """Base class for all commands."""

    PROGNAME = green
    VERSION = __version__ | blue
    COLOR_USAGE = green
    COLOR_GROUPS: ClassVar = {'Meta-switches': magenta, 'Switches': yellow, 'Subcommands': blue}
    SUBCOMMAND_HELPMSG = False


class Subcommand(Command):
    """Base class for all subcommands."""

    ALLOW_ABBREV = True  # incompatible with --help-all
    # TODO: plumbum issue about that, maybe


Subcommand.unbind_switches('help-all')


class SupportsNull:
    """Mixin for SubcommandOfNestedTextTo+SupportsTypes commands which support null."""

    null_paths = SwitchAttr(
        ('null', 'n'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as null, if it is an empty string",
    )


class SupportsDate:
    """Mixin for SubcommandOfNestedTextTo+SupportsTypes commands which support dates."""

    date_paths = SwitchAttr(
        ('date', 'd'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as a date, assuming it's ISO 8601",
    )


class SubcommandOfNestedTextTo(Subcommand):
    """Base class for all subcommands of NestedTextTo."""

    OTHER_FORMAT = "some other format"
    DOCSTRING_TMPL = "Read NestedText and output its content as {other_format}."
    DESCRIPTION_MORE_TMPL = """
Examples:
    - nt2 {subcommand} config.nt
    - cat config.nt | nt2 {subcommand}
"""

    def dump(
        self,
        *,
        input_files: LocalPath,
        dump_stdout: Callable[[TypedData], None],
        dump_str: Callable[[TypedData], str],
        fmt: str,
        converter: Converter,
        fix_data: Callable[[TypedData], TypedData] | None = None,
    ):
        r"""
        Read NestedText from stdin or ``input_files``, and send another format to stdout.

        Args:
            input_files: ``LocalPath``\ s with NestedText content.
            dump_stdout: A function to dump the data to stdout, plainly.
            dump_str: A function to dump the data to a string, also plain,
                for potential colorizing.
            fmt: The format to use for dumping (e.g., 'toml').
            converter: A ``Converter`` used to ``unstructure`` the result
                to match specific type support.
            fix_data: A function to fix the data, post-uptyping, if necessary.
        """
        dump_from_nestedtext(
            input_files=input_files,
            dump_stdout=dump_stdout,
            dump_str=dump_str,
            fmt=fmt,
            converter=converter,
            fix_data=fix_data,
        )


class ToNestedTextBase(Command):
    """Base class for commands that convert to NestedText."""

    inline_width = SwitchAttr(
        ('inline-width', 'i'),
        argtype=Range(0, 120),  # type: ignore
        default=0,
        argname='WIDTH',
        help="Maximum line width for inline dictionaries and lists",
    )
    to_schema = Flag(('to-schema', 's'), help="Rather than convert the inputs, generate a schema")

    def dump(
        self,
        *,
        load_stdin: Callable[[], TypedData],
        load_file: Callable[[LocalPath], TypedData],
        input_files: Sequence[LocalPath],
    ):
        r"""
        Convert inputs to NestedText or NestedText schema and dump to stdout.

        Args:
            input_files: ``LocalPath``\ s with typed data content.
            load_stdin: A function to load typed data from stdin.
            load_file: A function to load typed data from a ``LocalPath``.
        """
        kwargs = {'load_stdin': load_stdin, 'load_file': load_file, 'input_files': input_files}
        if not self.to_schema:
            dump_to_nestedtext(**kwargs, inline_width=cast(int, self.inline_width))
        else:
            dump_to_schema(**kwargs)


class SubcommandOfToNestedText(ToNestedTextBase, Subcommand):
    """Base class for all subcommands of ToNestedText."""

    OTHER_FORMAT = "some other format"
    DOCSTRING_TMPL = "Read {other_format} and output its content as NestedText."

    DESCRIPTION_MORE_TMPL = """
Examples:
    - 2nt {subcommand} config.{extension}
    - 2nt {subcommand} config.{extension} --to-schema >config.types.nt
    - cat config.{extension} | 2nt {subcommand}
"""


class SupportsTypes:
    """Mixin for SubcommandOfNestedTextTo commands which support types."""

    DESCRIPTION_MORE_TMPL = """
By default, generated {other_format} values will only contain strings, arrays, and maps,
but you can cast nodes matching YAML Paths to {types}.

Switches may be before or after file arguments.

Examples:
    - nt2 {subcommand} config.nt
    - nt2 {subcommand} config.nt --number font.size --boolean font.bold
    - nt2 {subcommand} config.nt --schema config.types.nt
    - cat config.nt | nt2 {subcommand}
"""

    schema_files: list[LocalPath] = SwitchAttr(
        ('schema', 's'),
        argtype=ExistingFile,  # type: ignore
        list=True,
        argname='NESTED_TEXT_FILE',
        help=(
            "Cast nodes matching YAML Path queries specified in a NestedText document. "
            "It must be a map whose keys are names of supported types "
            "(a subset of 'null', 'boolean', 'number', and 'date'). "
            "Each key's value is a list of YAML Paths"
        ),
    )
    bool_paths: list[str] = SwitchAttr(  # pyright: ignore [reportAssignmentType]
        ('boolean', 'b'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as boolean",
    )
    num_paths: list[str] = SwitchAttr(  # pyright: ignore [reportAssignmentType]
        ('number', 'int', 'float', 'i', 'f'),
        list=True,
        argname='YAMLPATH',
        help="Cast each node matching the given YAML Path query as a number",
    )

    def _yamlpaths(self) -> dict[str, list[str]]:
        # How risky is this, with unexpected *_paths attributes?
        return {attr: getattr(self, attr) for attr in dir(self) if attr.endswith('_paths')}

    def _absorb_schema_files(self):
        for schema_file in self.schema_files:
            schema = cast('Schema', nestedtext.load(schema_file))
            self.bool_paths = [*schema.get('boolean', ()), *self.bool_paths]
            self.num_paths = [*schema.get('number', ()), *self.num_paths]
            if isinstance(self, SupportsNull):
                self.null_paths = [*schema.get('null', ()), *self.null_paths]
            if isinstance(self, SupportsDate):
                self.date_paths = [*schema.get('date', ()), *self.date_paths]

    def dump(  # noqa: D102
        self,
        *,
        input_files: LocalPath,
        dump_stdout: Callable[[TypedData], None],
        dump_str: Callable[[TypedData], str],
        fmt: str,
        converter: Converter,
        fix_data: Callable[[TypedData], TypedData] | None = None,
    ):
        self._absorb_schema_files()
        dump_from_nestedtext(
            input_files=input_files,
            dump_stdout=dump_stdout,
            dump_str=dump_str,
            fmt=fmt,
            converter=converter,
            fix_data=fix_data,
            **self._yamlpaths(),
        )

    dump.__doc__ = SubcommandOfNestedTextTo.dump.__doc__


def description_more_for_supports_types(cls: Type[SupportsTypes]) -> Type[SupportsTypes]:  # noqa: UP006
    """
    Add DESCRIPTION_MORE to an nt2 subcommand class.

    Makes use of its ``OTHER_FORMAT`` and ``DESCRIPTION_MORE_TMPL`` attributes,
    as well as its mixin inheritance.

    Args:
        cls: A SubcommandOfNestedTextTo class which supports types.

    Returns:
        The same cls, with ``DESCRIPTION_MORE`` added.
    """
    type_names = ['boolean', 'number']
    if issubclass(cls, SupportsNull):  # pyright: ignore [reportArgumentType]
        type_names.append('null')
    if issubclass(cls, SupportsDate):
        type_names.append('date')
    types = f"{', '.join(type_names[:-1])} or {type_names[-1]}"

    name = cast('SubcommandOfNestedTextTo', cls).OTHER_FORMAT.lower()
    cls.DESCRIPTION_MORE = cls.DESCRIPTION_MORE_TMPL.format(  # pyright: ignore [reportAttributeAccessIssue]
        other_format=cls.OTHER_FORMAT,  # pyright: ignore [reportAttributeAccessIssue]
        subcommand=name,  # pyright: ignore [reportAttributeAccessIssue]
        types=types,
    )

    if name in ('json', 'toml', 'yaml'):
        cls.DESCRIPTION_MORE += (  # pyright: ignore [reportAttributeAccessIssue]
            f"\nIt can be invoked as either the subcommand `nt2 {name}`"
            f" or the single command `nt2{name}`.\n"
        )

    return cls


def description_more_for_2nt_subcommand(
    cls: Type[SubcommandOfToNestedText],  # noqa: UP006
) -> Type[SubcommandOfToNestedText]:  # noqa: UP006
    """
    Add DESCRIPTION_MORE to a 2nt subcommand class.

    Makes use of its ``OTHER_FORMAT`` and ``DESCRIPTION_MORE_TMPL`` attributes.

    Args:
        cls: A SubcommandOfToNestedText class.

    Returns:
        The same cls, with ``DESCRIPTION_MORE`` added.
    """
    name = cls.OTHER_FORMAT.lower()

    cls.DESCRIPTION_MORE = cls.DESCRIPTION_MORE_TMPL.format(  # pyright: ignore [reportAttributeAccessIssue]
        subcommand=name, extension={'yaml': 'yml'}.get(name, name)
    )

    if name in ('xml',):
        cls.DESCRIPTION_MORE = (  # pyright: ignore [reportAttributeAccessIssue]
            '\n'.join(
                line
                for line in cls.DESCRIPTION_MORE.splitlines()  # pyright: ignore [reportAttributeAccessIssue]
                if '--to-schema' not in line
            )
            + '\n'
        )

    if name in ('json', 'toml', 'yaml'):
        cls.DESCRIPTION_MORE += (  # pyright: ignore [reportOperatorIssue]
            f"\nIt can be invoked as either the subcommand `2nt {name}`"
            f" or the single command `{name}2nt`.\n"
        )

    return cls


def description_more_for_subcommand(
    cls: Type[SupportsTypes] | Type[SubcommandOfToNestedText],  # noqa: UP006
) -> Type[SupportsTypes] | Type[SubcommandOfToNestedText]:  # noqa: UP006
    """
    Add DESCRIPTION_MORE to a subcommand class.

    Dispatches to description_more_for_supports_types and description_more_for_2nt_subcommand.

    Args:
        cls: A SupportsTypes (and SubcommandOfNestedTextTo) or SubcommandOfToNestedText class.

    Returns:
        The same cls, with ``DESCRIPTION_MORE`` added.
    """
    if issubclass(cls, SupportsTypes):
        return description_more_for_supports_types(cls)
    if issubclass(cls, SubcommandOfToNestedText):
        return description_more_for_2nt_subcommand(cls)
    if issubclass(cls, SubcommandOfNestedTextTo):
        return description_more_for_supports_types(cls)  # works for now
    return cls


def docstring_for_subcommand(
    cls: Type[SubcommandOfNestedTextTo | SubcommandOfToNestedText],  # noqa: UP006
) -> Type[SubcommandOfNestedTextTo | SubcommandOfToNestedText]:  # noqa: UP006
    """
    Add a docstring to a subcommand class, using its ``DOCSTRING_TMPL`` and ``OTHER_FORMAT``.

    Args:
        cls: A SubcommandOfNestedTextTo or SubcommandOfToNestedText class.

    Returns:
        The same cls, with a docstring added.
    """
    cls.__doc__ = cls.DOCSTRING_TMPL.format(other_format=cls.OTHER_FORMAT)
    return cls


def invoke_ntt_command(
    command: Command, ntt_error_kwargs: dict[str, Any], *args: Any, **kwargs: Any
):
    """
    Invoke the command with the given arguments.

    Args:
        command: The command to invoke.
        ntt_error_kwargs: The keyword arguments to pass to the NTTError constructor.
        args: The positional arguments to pass to the command.
        kwargs: The keyword arguments to pass to the command.

    Raises:
        NTTError: If the command fails.
    """
    _, ret = command.invoke(*args, **kwargs)
    if ret:
        raise NTTError(**ntt_error_kwargs)


def get_ntt_stdout(
    command: Command, ntt_error_kwargs: dict[str, Any], *args: Any, **kwargs: Any
) -> str:
    """
    Return the stdout content from the given command invocation.

    Args:
        command: The command to invoke.
        ntt_error_kwargs: The keyword arguments to pass to the NTTError constructor.
        args: The positional arguments to pass to the command.
        kwargs: The keyword arguments to pass to the command.

    Returns:
        The stdout content from the given command invocation.

    Raises:
        NTTError: If the command fails.
        Exception: If the command raises a very unexpected exception.
    """
    sys_stdout = sys.stdout
    fake_stdout = io.StringIO()
    try:
        sys.stdout = fake_stdout
        _, ret = command.invoke(*args, **kwargs)
    except Exception:
        raise
    else:
        content = fake_stdout.getvalue()
    finally:
        sys.stdout = sys_stdout
        fake_stdout.close()
    if ret:
        raise NTTError(**ntt_error_kwargs)
    return content
