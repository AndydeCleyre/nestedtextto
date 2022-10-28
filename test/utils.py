"""A place for any shared functions used in tests."""
from __future__ import annotations

from collections.abc import Sequence

from nestedtext import load as ntload
from plumbum import LocalPath
from ward.expect import assert_equal


def assert_file_content(file: LocalPath, content: str):
    """
    Assert a file's contents match a string, forgiving different newline characters.

    Args:
        file: A path object to read the contents of
        content: A str to compare the file contents to
    """
    assert_equal(content.splitlines(), file.read('utf-8').splitlines(), "line for line")


def casting_args_from_schema_file(
    schema_file, types=('null', 'number', 'boolean')
) -> dict[str, Sequence[str]]:
    """
    Use a "schema file" to create a `dict` mapping internal option names to sequences of YAMLPaths.

    This can be unpacked and used to programmatically invoke `plumbum.cli.Application`s.

    Args:
        schema_file: A NestedText document (as accepted by `nestedtext.load`,
            such as a `pathlib.Path`), representing a map from type names
            ("null", "boolean", "number", "date") to lists of YAMLPaths to match against.
        types: An allow-list of types to include in the result
            (a subset of ("null", "boolean", "number", "date")).

    Returns:
        A `dict` mapping internal option names to sequences of YAMLPaths.
    """
    casting_args = {}
    schema_data = ntload(schema_file)
    attr_names = {
        'null': 'null_paths',
        'boolean': 'bool_paths',
        'number': 'num_paths',
        'date': 'date_paths',
    }
    for cast_type in types:
        casting_args[attr_names[cast_type]] = schema_data.get(cast_type, ())
    return casting_args
