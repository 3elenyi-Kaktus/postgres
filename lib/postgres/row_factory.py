from typing import Any, Sequence
from typing_extensions import Self

from psycopg import AsyncClientCursor
from psycopg.rows import RowMaker


class Factory:
    def __init__(self, _) -> None:
        pass

    @classmethod
    def row_factory(cls, cursor: AsyncClientCursor[Any]) -> RowMaker[Self]:
        columns: list[str] = [column.name for column in cursor.description]

        def make_row(values: Sequence[Any]) -> Self:
            row: dict[str, Any] = dict(zip(columns, values))
            return cls(**row)

        return make_row
