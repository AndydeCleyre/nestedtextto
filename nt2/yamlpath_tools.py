"""
Convenient functions for making use of yamlpath.

- ``mk_yamlpath_processor``
- ``non_null_matches``
"""
from __future__ import annotations

import sys
from collections.abc import Iterable
from types import SimpleNamespace

from ruamel.yaml.main import YAML
from yamlpath import Processor
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
