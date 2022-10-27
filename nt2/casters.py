"""
Provide any functions for transforming a "stringy" ``dict``/``list`` to one with more types.

In practice, this is just `cast_stringy_data` and any support functions it needs.
"""
from __future__ import annotations

import sys
from collections.abc import Iterable, Sequence
from datetime import date, datetime, time
from types import SimpleNamespace
from uuid import uuid4

from yamlpath import Processor as YPProcessor
from yamlpath.exceptions import YAMLPathException
from yamlpath.wrappers import ConsolePrinter as YPConsolePrinter
from yamlpath.wrappers.nodecoords import NodeCoords

from .converters import Converter, mk_json_types_converter, mk_marked_string_converter

StringyDatum = 'str | list | dict'
StringyData = 'list[StringyDatum] | dict[str, StringyDatum]'


def _str_to_bool(informal_bool: str) -> bool:
    """
    Translate a commonly used boolean ``str`` into a real ``bool``.

    Args:
        informal_bool: A boolean represented as ``str``, like ``"true"``, ``"no"``, ``"off"``, etc.

    Returns:
        ``True`` or ``False`` to match the intent of ``informal_bool``.

    Raises:
        ValueError: This doesn't look like enough like a ``bool`` to translate.
    """
    if informal_bool.lower() in ('true', 'yes', 'y', 'on', '1'):
        return True
    if informal_bool.lower() in ('false', 'no', 'n', 'off', '0'):
        return False
    raise ValueError  # pragma: no cover


def _str_to_num(informal_num: str) -> int | float:
    """
    Translate a number as ``str`` into a real ``int`` or ``float``.

    Args:
        informal_num: A number represented as ``str``, like ``"5.5"``, ``"1e3"``, or ``"0xdecaf"``

    Returns:
        An ``int`` or ``float`` equivalent of ``informal_num``.

    Raises:
        ValueError: This doesn't look like enough like a number to translate.
    """
    try:
        num = float(informal_num)
    except ValueError as e:
        for prefix, base in {'0x': 16, '0o': 8, '0b': 2}.items():
            if informal_num.lower().startswith(prefix):
                try:
                    num = int(informal_num, base)
                except Exception:  # pragma: no cover
                    raise ValueError(': '.join(e.args))
                else:
                    return num
        raise e  # pragma: no cover
    try:
        inum = int(num)
    except (ValueError, OverflowError):
        return num
    else:
        return inum if num == inum else num


def _non_null_matches(surgeon: YPProcessor, *query_paths: str) -> Iterable[NodeCoords]:
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


def cast_stringy_data(
    data: StringyData,
    bool_paths: Sequence[str] = (),
    null_paths: Sequence[str] = (),
    num_paths: Sequence[str] = (),
    date_paths: Sequence[str] = (),
    converter: Converter | None = None,
) -> list | dict:
    r"""
    Take nested ``StringyData`` and return a copy with matching nodes up-typed.

    Args:
        data: A ``dict`` or ``list`` composed of ``str``, ``dict`` and ``list`` items
            all the way down.
        bool_paths: YAMLPath queries indicating nodes to be up-typed to ``bool``.
        null_paths: YAMLPath queries indicating nodes to be up-typed to ``None``.
        num_paths: YAMLPath queries indicating nodes to be up-typed to ``int``/``float``.
        date_paths: YAMLPath queries indicating nodes to be up-typed to
            ``date``/``datetime``/``time``.
        converter: A ``Converter`` used to ``unstructure`` the result
            to match specific type support,
            defaulting to one created with `mk_json_types_converter`.

    Returns:
        A nested ``dict`` or ``list`` containing some "up-typed" (casted) items
            in addition to ``str``\ s.

    Raises:
        ValueError: Up-typing a ``str`` failed due to an unexpected format.
        Exception: An unexpected problem.
    """
    doc = dict(data) if isinstance(data, dict) else list(data)

    if not any((bool_paths, null_paths, num_paths, date_paths)):
        return doc

    log = YPConsolePrinter(SimpleNamespace(quiet=True, verbose=False, debug=False))
    surgeon = YPProcessor(log, doc)

    for match in _non_null_matches(surgeon, *null_paths):
        if match.node == '':
            surgeon.set_value(match.path, None)

    for match in _non_null_matches(surgeon, *bool_paths):
        if not isinstance(match.node, str):
            continue
        try:
            surgeon.set_value(match.path, _str_to_bool(match.node))
        except ValueError as e:  # pragma: no cover
            raise ValueError(': '.join((*e.args, str(match.path))))

    for match in _non_null_matches(surgeon, *num_paths):
        if not isinstance(match.node, str):
            continue
        try:
            num = _str_to_num(match.node)
        except ValueError as e:  # pragma: no cover
            raise ValueError(': '.join(e.args + (str(match.path),)))
        else:
            surgeon.set_value(match.path, num)

    # We can't currently store a time type in the
    # intermediary YAML doc object, so:
    marked_times_present = False
    time_marker = str(uuid4())
    marked_time_converter = mk_marked_string_converter(time_marker=time_marker)

    for match in _non_null_matches(surgeon, *date_paths):
        if not isinstance(match.node, str) or match.node.startswith(time_marker):
            continue
        try:
            val = date.fromisoformat(match.node)
        except ValueError:
            try:
                val = datetime.fromisoformat(match.node)
            except ValueError:
                try:
                    val = time.fromisoformat(match.node)
                except Exception as e:  # pragma: no cover
                    raise e
                else:
                    val = f"{time_marker}{val.isoformat()}"
                    marked_times_present = True
        surgeon.set_value(match.path, val)

    if marked_times_present:
        doc = marked_time_converter.unstructure(doc)

    return (converter or mk_json_types_converter()).unstructure(doc)
