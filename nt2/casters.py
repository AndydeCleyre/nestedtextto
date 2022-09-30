import sys
from collections.abc import Sequence
from datetime import date, datetime, time
from types import SimpleNamespace

from yamlpath import Processor as YPProcessor
from yamlpath.exceptions import YAMLPathException
from yamlpath.wrappers import ConsolePrinter as YPConsolePrinter

from .converters import Converter, mk_json_types_converter

StringyDatum = str | list | dict
StringyData = list[StringyDatum] | dict[str, StringyDatum]


def str_to_bool(value: str) -> bool:
    if value.lower() in ('true', 'yes', 'y', 'on', '1'):
        return True
    if value.lower() in ('false', 'no', 'n', 'off', '0'):
        return False
    raise ValueError


def non_null_matches(surgeon, *query_paths):
    for query_path in query_paths:
        try:
            matches = [m for m in surgeon.get_nodes(query_path) if m.node is not None]
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
        try:
            surgeon.set_value(match.path, str_to_bool(match.node))
        except ValueError as e:
            raise ValueError(': '.join((*e.args, str(match.path))))

    for match in non_null_matches(surgeon, *num_paths):
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

    for match in non_null_matches(surgeon, *date_paths):
        try:
            val = date.fromisoformat(match.node)
        except ValueError:
            try:
                val = datetime.fromisoformat(match.node)
            except ValueError:
                # val = time.fromisoformat(match.node)
                # We can't currently store a time type in the
                # intermediary YAML doc object, so:
                val = str(time.fromisoformat(match.node))
        surgeon.set_value(match.path, val)

    return (converter or mk_json_types_converter()).unstructure(doc)
