import io
import sys

from plumbum.cli import Application

from nt2.ui import (
    JSONToNestedText, NestedTextToJSON, NestedTextToTOML,
    NestedTextToYAML, TOMLToNestedText, YAMLToNestedText
)


def run_app(app_class: Application, *cli_args, **cli_kwargs):
    sys_stdout = sys.stdout
    try:
        fake_stdout = io.StringIO()
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


def json2nt(*cli_args, **cli_kwargs):
    return run_app(JSONToNestedText, *cli_args, **cli_kwargs)


def nt2json(*cli_args, **cli_kwargs):
    return run_app(NestedTextToJSON, *cli_args, **cli_kwargs)


def nt2yaml(*cli_args, **cli_kwargs):
    return run_app(NestedTextToYAML, *cli_args, **cli_kwargs)


def yaml2nt(*cli_args, **cli_kwargs):
    return run_app(YAMLToNestedText, *cli_args, **cli_kwargs)


def nt2toml(*cli_args, **cli_kwargs):
    return run_app(NestedTextToTOML, *cli_args, **cli_kwargs)


def toml2nt(*cli_args, **cli_kwargs):
    return run_app(TOMLToNestedText, *cli_args, **cli_kwargs)
