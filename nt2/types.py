"""TypeAliases for internal use."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date, datetime, time

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias


JSONData: TypeAlias = 'dict[str, JSONData] | list[JSONData] | str | int | float | bool | None'
YAMLData: TypeAlias = (
    'dict[str, YAMLData] | list[YAMLData] | str | int | float | bool | None | datetime | date'
)
TOMLData: TypeAlias = (
    'TOMLHashData | list[TOMLData] | str | int | float | bool | datetime | date | time'
)
TOMLHashData: TypeAlias = dict[str, TOMLData]

StringyData: TypeAlias = 'str | list[StringyData] | dict[str, StringyData]'

SchemaKey: TypeAlias = Literal['number', 'boolean', 'null', 'date']
Schema: TypeAlias = dict[SchemaKey, list[str]]

SchemaNative: TypeAlias = 'int | float | bool | None | datetime | date | time'
TypedData: TypeAlias = (
    'dict[str, TypedData] | list[TypedData] | SchemaNative | JSONData | YAMLData | TOMLData'
)
