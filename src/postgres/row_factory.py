from typing import Any, Sequence

from psycopg import AsyncClientCursor
from psycopg.rows import RowMaker
from typing_extensions import Self


class Factory:
    def __init__(self, _: Any) -> None:
        pass

    @classmethod
    def row_factory(cls, cursor: AsyncClientCursor[Any]) -> RowMaker[Self]:
        columns: list[str] = []
        if cursor.description is not None:
            columns = [column.name for column in cursor.description]

        def make_row(values: Sequence[Any]) -> Self:
            row: dict[str, Any] = dict(zip(columns, values))
            return cls(**row)

        return make_row
