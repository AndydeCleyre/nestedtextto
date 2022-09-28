import sys
from collections.abc import Sequence
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

    for query_path in null_paths:
        try:
            matches = [*surgeon.get_nodes(query_path)]
        except YAMLPathException as e:
            print(*e.args, sep='\n', file=sys.stderr)
            continue
        for match in matches:
            if not match.node:
                surgeon.set_value(match.path, None)

    for query_path in bool_paths:
        try:
            matches = [*surgeon.get_nodes(query_path)]
        except YAMLPathException as e:
            print(*e.args, sep='\n', file=sys.stderr)
            continue
        for match in matches:
            if match.node is not None:
                try:
                    surgeon.set_value(match.path, str_to_bool(match.node))
                except ValueError as e:
                    raise ValueError(': '.join((*e.args, str(match.path))))
    for query_path in num_paths:
        try:
            matches = [*surgeon.get_nodes(query_path)]
        except YAMLPathException as e:
            print(*e.args, sep='\n', file=sys.stderr)
            continue
        for match in matches:
            if match.node is not None:
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

    # TODO: maybe pull some logic out of this method to a smaller reusable snippet:
    # something(query_path, )

    # TODO: We can't yet manage setting a date/datetime object with surgeon.set_value...

    return (converter or mk_json_types_converter()).unstructure(doc)
