"""
Provide any functions for transforming a "stringy" ``dict``/``list``/value to one with more types.

In practice, this is just `cast_stringy_data` and any support functions it needs.
"""

from __future__ import annotations

import re
from datetime import date, datetime, time
from typing import TYPE_CHECKING, cast
from uuid import uuid4

from .converters import mk_json_types_converter, mk_unyamlable_converter
from .yamlpath_tools import Processor, mk_yamlpath_processor, non_null_matches

if TYPE_CHECKING:
    from typing import Sequence

    from .converters import Converter
    from .types import StringyData, TypedData
    from .yamlpath_tools import YAMLPath


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
    if informal_bool.lower() in ('true', 't', 'yes', 'y', 'on', '1'):
        return True
    if informal_bool.lower() in ('false', 'f', 'no', 'n', 'off', '0'):
        return False
    raise ValueError(f"{informal_bool} doesn't look like a boolean")


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
            if re.match(f"[+-]?{prefix}", informal_num, re.IGNORECASE):
                try:
                    num = int(informal_num, base)
                except Exception:
                    raise ValueError(': '.join(e.args)) from None
                else:
                    return num
        raise
    return int(num) if num.is_integer() else num


def _str_to_datey(informal_datey: str, time_marker: str) -> date | datetime | str:
    """
    Translate an ISO 8601 date/time ``str`` into a ``date``, ``datetime``, or marked time ``str``.

    Args:
        informal_datey: An ISO 8601 date/time ``str``.
        time_marker: An arbitrary prefix (such as a UUID) which will be used
            to create a "marked time" ``str``, rather than an (unyamlable) ``time`` instance.

    Returns:
        A ``date``, ``datetime``, or marked time ``str`` equivalent of ``informal_datey``.
            A marked time ``str`` is just ISO 8601 prefixed with ``time_marker``.

    Raises:
        ValueError: This doesn't look like enough like a date/time to translate.
    """
    try:
        return date.fromisoformat(informal_datey)
    except ValueError:
        try:
            return datetime.fromisoformat(informal_datey)
        except ValueError:
            try:
                val = time.fromisoformat(informal_datey)
            except Exception as e:
                raise ValueError(': '.join(e.args)) from None
            else:
                return f"{time_marker}{val.isoformat()}"


def _cast_datey(surgeon: Processor, date_paths: Sequence[str]) -> dict | list:
    r"""
    Cast ``date``/``datetime``/``time`` strings to ``date``/``datetime``/``time`` objects.

    We can't currently store a time type in the intermediary YAML doc object (``surgeon.data``),
    so we mark times as special ``str``\ s within ``surgeon.data``,
    then do a second pass to convert them to ``time`` objects on the way out.

    Args:
        surgeon: A YAMLPath ``Processor`` with existing ``data`` to be up-typed.
        date_paths: YAMLPath queries indicating nodes to be up-typed to
            ``date``/``datetime``/``time``.

    Returns:
        A nested ``dict`` or ``list`` containing some "up-typed" (casted) items
            in addition to ``str``\ s.

    Raises:
        ValueError: Up-typing a ``str`` failed due to an unexpected format.
    """
    marked_times_present = False
    time_marker = str(uuid4())

    for match in non_null_matches(surgeon, *date_paths):
        if not isinstance(match.node, str) or match.node.startswith(time_marker):
            continue
        try:
            datey = _str_to_datey(match.node, time_marker)
        except ValueError as e:
            raise ValueError(': '.join((*e.args, str(match.path)))) from e
        else:
            surgeon.set_value(cast('YAMLPath', match.path), datey)
            if not marked_times_present and isinstance(datey, str):
                marked_times_present = True

    if marked_times_present:
        marked_time_converter = mk_unyamlable_converter(time_marker=time_marker)
        return marked_time_converter.unstructure(surgeon.data)
    return surgeon.data


def cast_stringy_data(
    data: StringyData,
    bool_paths: Sequence[str] = (),
    null_paths: Sequence[str] = (),
    num_paths: Sequence[str] = (),
    date_paths: Sequence[str] = (),
    converter: Converter | None = None,
) -> TypedData:
    r"""
    Take nested ``StringyData`` and return a copy with matching nodes up-typed.

    Args:
        data: A ``dict`` or ``list`` composed of ``str``, ``dict`` and ``list`` items
            all the way down, or (rarely) a ``str``.
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
            in addition to ``str``\ s, or (rarely) a single value.

    Raises:
        ValueError: Up-typing a ``str`` failed due to an unexpected format.
    """
    doc = dict(data) if isinstance(data, dict) else list(data) if isinstance(data, list) else data  # pyright: ignore [reportArgumentType, reportCallIssue]

    if not any((bool_paths, null_paths, num_paths, date_paths)):
        return cast('TypedData', doc)

    surgeon = mk_yamlpath_processor(doc)  # pyright: ignore [reportArgumentType]

    for match in non_null_matches(surgeon, *null_paths):
        if match.node == '':
            surgeon.set_value(cast('YAMLPath', match.path), None)

    for match in non_null_matches(surgeon, *bool_paths):
        if not isinstance(match.node, str):
            continue
        try:
            surgeon.set_value(cast('YAMLPath', match.path), _str_to_bool(match.node))
        except ValueError as e:
            raise ValueError(': '.join((*e.args, str(match.path)))) from e

    for match in non_null_matches(surgeon, *num_paths):
        if not isinstance(match.node, str):
            continue
        try:
            surgeon.set_value(cast('YAMLPath', match.path), _str_to_num(match.node))
        except ValueError as e:
            raise ValueError(': '.join((*e.args, str(match.path)))) from e

    doc = _cast_datey(surgeon, date_paths)

    return (converter or mk_json_types_converter()).unstructure(doc)
