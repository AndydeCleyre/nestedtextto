from __future__ import annotations

import sys
from collections.abc import Sequence
from datetime import date, datetime, time
from types import SimpleNamespace
from uuid import uuid4

from yamlpath import Processor as YPProcessor
from yamlpath.exceptions import YAMLPathException
from yamlpath.wrappers import ConsolePrinter as YPConsolePrinter

from .converters import Converter, mk_json_types_converter, mk_marked_string_converter

StringyDatum = 'str | list | dict'
StringyData = 'list[StringyDatum] | dict[str, StringyDatum]'


def str_to_bool(value: str) -> bool:
    if value.lower() in ('true', 'yes', 'y', 'on', '1'):
        return True
    if value.lower() in ('false', 'no', 'n', 'off', '0'):
        return False
    raise ValueError


def non_null_matches(surgeon, *query_paths):
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
    doc = dict(data) if isinstance(data, dict) else list(data)

    if not any((bool_paths, null_paths, num_paths, date_paths)):
        return doc

    log = YPConsolePrinter(SimpleNamespace(quiet=True, verbose=False, debug=False))
    surgeon = YPProcessor(log, doc)

    for match in non_null_matches(surgeon, *null_paths):
        if match.node == '':
            surgeon.set_value(match.path, None)

    for match in non_null_matches(surgeon, *bool_paths):
        if not isinstance(match.node, str):
            continue
        try:
            surgeon.set_value(match.path, str_to_bool(match.node))
        except ValueError as e:
            raise ValueError(': '.join((*e.args, str(match.path))))

    for match in non_null_matches(surgeon, *num_paths):
        if not isinstance(match.node, str):
            continue
        try:
            num = float(match.node)
        except ValueError as e:
            raise ValueError(': '.join((*e.args, str(match.path))))
        try:
            inum = int(num)
        except ValueError:
            surgeon.set_value(match.path, num)
        else:
            surgeon.set_value(match.path, inum if num == inum else num)

    # We can't currently store a time type in the
    # intermediary YAML doc object, so:
    marked_times_present = False
    time_marker = str(uuid4())
    marked_time_converter = mk_marked_string_converter(time_marker=time_marker)

    for match in non_null_matches(surgeon, *date_paths):
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
                except Exception as e:
                    raise e
                else:
                    val = f"{time_marker}{val.isoformat()}"
                    marked_times_present = True
        surgeon.set_value(match.path, val)

    if marked_times_present:
        doc = marked_time_converter.unstructure(doc)

    return (converter or mk_json_types_converter()).unstructure(doc)
