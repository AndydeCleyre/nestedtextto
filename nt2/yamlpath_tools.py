"""Convenient functions for making use of yamlpath."""
from __future__ import annotations

import sys
from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime, time
from types import SimpleNamespace

try:
    from types import NoneType
except ImportError:
    NoneType = type(None)

from ruamel.yaml.main import YAML
from yamlpath import Processor, YAMLPath
from yamlpath.common import Parsers
from yamlpath.exceptions import YAMLPathException
from yamlpath.wrappers import ConsolePrinter
from yamlpath.wrappers.nodecoords import NodeCoords


def mk_yaml_editor() -> YAML:
    """
    Construct a YAML editor with ``load`` and ``dump`` methods.

    Returns:
        A configured object able to ``.load`` and ``.dump`` YAML (``ruamel.yaml.main.YAML``).
    """
    editor = Parsers.get_yaml_editor()
    editor.indent(mapping=2, sequence=4, offset=2)
    return editor


def mk_yamlpath_processor(data: dict | list) -> Processor:
    """
    Construct a YAML Path processor/document for the ``data``.

    Args:
        data: An object from which to create the processor, or "surgeon."

    Returns:
        A document object able to ``.set_value`` and ``.get_nodes`` (``yamlpath.Processor``).
    """
    log = ConsolePrinter(SimpleNamespace(quiet=True, verbose=False, debug=False))
    return Processor(log, data)


def non_null_matches(surgeon: Processor, *query_paths: str) -> Iterable[NodeCoords]:
    r"""
    Generate ``NodeCoords`` matching any ``query_paths``.

    Omit any matches whose ``node`` attr is ``None``.

    Args:
        surgeon: A ``yamlpath.Processor``, already storing the YAML document to be queried.
        query_paths: YAMLPath query ``str``\ s to find matches for in the document.

    Yields:
        Matching ``NodeCoords`` items from the document,
            each having a ``node`` (value) attribute and ``path`` (YAMLPath) attribute.
    """
    for query_path in query_paths:
        try:
            matches = [
                m for m in surgeon.get_nodes(query_path, mustexist=True) if m.node is not None
            ]
        except YAMLPathException as e:
            print(*e.args, sep='\n', file=sys.stderr)
            continue
        else:
            yield from matches


def _schema_entry_type(obj: int | float | bool | None | datetime | date | time):
    # -> Literal['number', 'boolean', 'null', 'date']
    if isinstance(obj, bool):
        return 'boolean'
    if isinstance(obj, (int, float)):
        return 'number'
    if isinstance(obj, NoneType):
        return 'null'
    if isinstance(obj, (datetime, date, time)):
        return 'date'
    raise ValueError(f"Can't match {type(obj)} ({obj}) to 'number', 'boolean', 'null', or 'date'")


def typed_data_to_schema(data: dict | list) -> dict:
    """
    Analyze nested data and produce a matching schema document.

    Args:
        data: A nested data object whose elements can be mapped to schema entries.

    Returns:
        A schema ``dict`` mapping ('number', 'boolean', 'null', or 'date') to lists of YAML Paths.
    """
    schema = defaultdict(list)
    surgeon = mk_yamlpath_processor(data)
    for match in surgeon.get_nodes('/**'):
        if isinstance(match.node, str):
            continue
        schema[_schema_entry_type(match.node)].append(str(match.path))
    return schema


def guess_briefer_schema(schema: dict[str, list[str]]) -> dict[str, list[str]]:
    """
    Suggest an alternative schema, with low confidence.

    Args:
        schema: A map of type names ('date', 'boolean', 'number', 'null') to lists of YAML Paths.

    Returns:
        A dumb guess at an alternative schema that matches more patterns and fewer literal paths.
    """
    briefer_schema = {}
    for vartype, ypaths in schema.items():
        pattern_paths = set()
        for ypath in map(YAMLPath, ypaths):
            segments = [seg[-1] for seg in ypath.unescaped if isinstance(seg[-1], str)]
            sep = str(ypath.seperator)  # sic
            entry = f"{sep if sep == '/' else ''}{sep.join(segments)}"
            pattern_paths.add(entry)
        briefer_schema[vartype] = list(pattern_paths)
    return briefer_schema
