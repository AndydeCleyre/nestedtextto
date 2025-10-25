"""Exception definitions and pretty-printing."""

from __future__ import annotations

import sys
from functools import singledispatch
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable
import wrapt
from plumbum.colors import (
    blue,  # pyright: ignore [reportAttributeAccessIssue]
    green,  # pyright: ignore [reportAttributeAccessIssue]
    red,  # pyright: ignore [reportAttributeAccessIssue]
    yellow,  # pyright: ignore [reportAttributeAccessIssue]
)
from rich import inspect as _rich_inspect
from rich.console import Console as RichConsole


def docstring_for_NTTError_from(func: Callable) -> Callable:  # noqa: N802
    """
    Add a docstring to an NT2Error_from function.

    Args:
        func: An NT2Error_from function.

    Returns:
        The same function, with a new docstring.
    """
    func.__doc__ = """
Return an NT2Error from a {from_error}.

Args:
    exc: A {from_error}.

Returns:
    An NT2Error with the same details.
""".format(from_error=func.__annotations__['exc'])
    return func


class NTTError(Exception):
    """An error class we can control and pretty-print."""

    def __init__(
        self,
        title: str | None = None,
        summary: str | None = None,
        file: str | None = None,
        content: tuple[str] | None = None,
        suggestion: str | None = None,
    ):
        """
        Return an NTTError, with a pretty __str__ method.

        Args:
            title: The title of the error.
            summary: A summary of the error.
            file: The source, usually a filename, potentially with :lineno:colno suffix.
            content: Miscellaneous extra lines to print.
            suggestion: A suggestion for how to fix the error.
        """
        self.title = title
        self.summary = summary
        self.file = file
        self.content = content
        self.suggestion = suggestion
        super().__init__(': '.join(msg for msg in (title, summary) if msg))

    def __str__(self) -> str:
        """
        Return a pretty string with all our details.

        Returns:
            A pretty string.
        """
        lines = [f"-- {self.title or 'NestedTextTo'} --" | red]
        if self.summary:
            lines.append(f"  {self.summary}" | yellow)
        if self.file:
            lines.append(("  File: " | blue) + self.file)
        if self.content:
            lines.extend(("  > " | yellow) + c for c in self.content)
        if self.suggestion:
            lines.append(("  Suggestion: " | green) + self.suggestion)
        return '\n'.join(lines)


def mk_require_support(*, format_name: str, supported: bool, extras_name: str) -> Callable:
    """
    Return a decorator that raises an exception if format_name support is not installed.

    Args:
        format_name: The name of the format.
        supported: Whether the format is supported.
        extras_name: The name of the corresponding extras in the Python package.

    Returns:
        A decorator that raises an exception if format_name support is not installed.
    """

    @wrapt.decorator
    def require_support(wrapped, instance, args, kwargs):  # type: ignore  # noqa: ANN001, ANN202, ARG001
        if not supported:
            raise NTTError(
                title=f"{format_name} support for NestedTextTo is not installed",
                suggestion=f"Reinstall as 'nt2[{extras_name}]' or 'nt2[all]'",
            )
        return wrapped(*args, **kwargs)

    require_support.__doc__ = f"""
If {format_name} support is not installed, raise an exception.

Raises:
    NTTError: The libraries for {format_name} support are absent.

# noqa: DAR101 wrapped instance args kwargs
# noqa: DAR201
"""
    return require_support


@singledispatch
def NTTError_from(exc: Exception) -> NTTError:  # noqa: N802
    """
    Return an NTTError based on the exception if possible.

    Otherwise, raise the original exception.

    Args:
        exc: Any exception.

    Raises:
        exc: If exc can't be converted to an NTTError.
    """
    raise exc


@NTTError_from.register
def NTTError_from_NTTError(exc: NTTError) -> NTTError:  # noqa: N802
    """
    Return exc, as-is.

    This allows us to uniformly handle exceptions that are already NTTErrors.

    Args:
        exc: An NTTError.

    Returns:
        NTTError: The same NTTError.
    """
    return exc


def inspect_exception(exc: Exception):
    """
    Pretty-print an exception to stderr for the user to see.

    Args:
        exc: Any ``Exception``. After printing, it is swallowed, not raised.
    """
    try:
        print(NTTError_from(exc), file=sys.stderr)
    except:  # noqa: E722
        _rich_inspect(exc, console=RichConsole(stderr=True), value=False)


@wrapt.decorator
def friendly_exceptions(wrapped, instance, args, kwargs):  # type: ignore  # noqa: ANN001,ARG001,ANN201
    """
    Catch and pretty-print any exceptions when calling.

    # noqa: DAR101 wrapped args instance kwargs
    # noqa: DAR201
    """
    try:
        return wrapped(*args, **kwargs)
    except Exception as e:
        inspect_exception(e)
        return 1
