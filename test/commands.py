"""
Functions representing the CLI apps, in a form more suitable for testing.

If the tests were to invoke the apps as imported from `plumbum.cmd`,
measuring coverage would be tricky.

If they invoked the apps via directly imported forms,
capturing stdout would be tricky and repetitive.

Each version herein returns the stdout as a `str` for convenience in tests.
"""
import io
import sys

from plumbum.cli import Application

from nt2.ui import (
    JSONToNestedText, NestedTextToJSON, NestedTextToTOML,
    NestedTextToYAML, TOMLToNestedText, YAMLToNestedText
)


def _run_app(app_class: Application, *cli_args, **cli_kwargs) -> str:
    """
    Invoke `app_class` with given flags, and return stdout content.

    Args:
        app_class: A `plumbum.cli.Application` to invoke.
        cli_args: Positional arguments to pass to `app_class`.
        cli_kwargs: Named arguments to pass to `app_class`, using *internal* names.

    Returns:
        The content of (fake) stdout after invoking `app_class`.

    Raises:
        Exception: Unexpected problem during invocation.
    """
    sys_stdout = sys.stdout
    fake_stdout = io.StringIO()
    try:
        sys.stdout = fake_stdout
        app, main_result = app_class.invoke(*cli_args, **cli_kwargs)
    except Exception as e:
        raise e
    else:
        output = fake_stdout.getvalue()
    finally:
        sys.stdout = sys_stdout
        fake_stdout.close()
    return output


def json2nt(*cli_args, **cli_kwargs) -> str:
    """
    Invoke `JSONToNestedText` in a test-friendly way.

    Args:
        cli_args: Positional arguments.
        cli_kwargs: Named options, using *internal* names.

    Returns:
        The content of (fake) stdout after invoking `JSONToNestedText`.
    """
    return _run_app(JSONToNestedText, *cli_args, **cli_kwargs)


def nt2json(*cli_args, **cli_kwargs) -> str:
    """
    Invoke `NestedTextToJSON` in a test-friendly way.

    Args:
        cli_args: Positional arguments.
        cli_kwargs: Named options, using *internal* names.

    Returns:
        The content of (fake) stdout after invoking `NestedTextToJSON`.
    """
    return _run_app(NestedTextToJSON, *cli_args, **cli_kwargs)


def nt2yaml(*cli_args, **cli_kwargs) -> str:
    """
    Invoke `NestedTextToYAML` in a test-friendly way.

    Args:
        cli_args: Positional arguments.
        cli_kwargs: Named options, using *internal* names.

    Returns:
        The content of (fake) stdout after invoking `NestedTextToYAML`.
    """
    return _run_app(NestedTextToYAML, *cli_args, **cli_kwargs)


def yaml2nt(*cli_args, **cli_kwargs) -> str:
    """
    Invoke `YAMLToNestedText` in a test-friendly way.

    Args:
        cli_args: Positional arguments.
        cli_kwargs: Named options, using *internal* names.

    Returns:
        The content of (fake) stdout after invoking `YAMLToNestedText`.
    """
    return _run_app(YAMLToNestedText, *cli_args, **cli_kwargs)


def nt2toml(*cli_args, **cli_kwargs) -> str:
    """
    Invoke `NestedTextToTOML` in a test-friendly way.

    Args:
        cli_args: Positional arguments.
        cli_kwargs: Named options, using *internal* names.

    Returns:
        The content of (fake) stdout after invoking `NestedTextToTOML`.
    """
    return _run_app(NestedTextToTOML, *cli_args, **cli_kwargs)


def toml2nt(*cli_args, **cli_kwargs) -> str:
    """
    Invoke `TOMLToNestedText` in a test-friendly way.

    Args:
        cli_args: Positional arguments.
        cli_kwargs: Named options, using *internal* names.

    Returns:
        The content of (fake) stdout after invoking `TOMLToNestedText`.
    """
    return _run_app(TOMLToNestedText, *cli_args, **cli_kwargs)
