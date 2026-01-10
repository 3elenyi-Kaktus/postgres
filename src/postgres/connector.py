import logging
from pathlib import Path
from time import sleep
from typing import Any, Callable, Iterable, Optional

import psycopg
from psycopg import AsyncClientCursor, AsyncConnection
from psycopg.abc import Query
from psycopg.rows import AsyncRowFactory, Row, tuple_row
from psycopg_pool.pool_async import AsyncConnectionPool
from typing_extensions import Self


class DBConnector:
    def __init__(self, database: str, user: str, password: str, host: str, port: int):
        logging.info(
            f"Initializing DB connector with:\n"
            f"Database: {database}\n"
            f"User: {user}\n"
            f"Password: {password}\n"
            f"Host: {host}\n"
            f"Port: {port}"
        )

        if database is None or user is None or password is None or host is None or port is None:
            raise RuntimeError(f"All arguments must be present")

        self.aconn: AsyncConnection = None
        self.dbname = database
        self.user = user
        self.password = password
        self.host = host
        self.port = port

    @classmethod
    async def create(cls, *args, **kwargs) -> Self:
        connector: cls = cls(*args, **kwargs)
        await connector.connect()
        return connector

    async def connect(self) -> None:
        while True:
            logging.info(f"Try to connect to Postgres DB")
            try:
                self.aconn = await AsyncConnection.connect(
                    dbname=self.dbname,
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port,
                    autocommit=True,
                    cursor_factory=AsyncClientCursor,
                )
                logging.info(f"Connected to Postgres DB successfully")
                break
            except psycopg.Error as exc:
                logging.info(f"Can`t establish connection to database, retry in 3 sec. Reason: {exc}")
                sleep(3)

    @staticmethod
    def checkConnection(func: Callable):
        async def wrapper(self, *args, **kwargs):
            try:
                await AsyncConnectionPool.check_connection(self.aconn)
            except BaseException as exc:
                logging.error(f"Connections to DB seems to be broken, try to recreate it")
                logging.exception(exc)
                await self.connect()
            return await func(self, *args, **kwargs)

        return wrapper

    @checkConnection
    async def executeSQL(
        self,
        sql: Query,
        request: dict[str, Any] = None,
        row_factory: AsyncRowFactory = tuple_row,
        fetchable: bool = True,
    ) -> Optional[list[Row]]:
        async with AsyncClientCursor(self.aconn, row_factory=row_factory) as cursor:
            try:
                await cursor.execute(query=sql, params=request)
                if not fetchable:
                    logging.debug(f"Query completed, marked as unfetchable")
                    return None
                result: list[Row] = await cursor.fetchall()
            except psycopg.Error as exc:
                logging.error(f"Failed to execute query")
                raise RuntimeError(f"Failed to execute query") from exc

        logging.debug(f"Query result: {result}")
        return result

    @checkConnection
    async def copyFromFileSQL(self, sql: Query, filepath: Path) -> None:
        try:
            with open(filepath, "rt") as file:
                async with AsyncClientCursor(self.aconn) as cursor:
                    async with cursor.copy(sql) as copy:
                        while data := file.read(1024**2):
                            await copy.write(data)
        except OSError as error:
            logging.error(f"Failed to read file at: {filepath}")
            raise RuntimeError(f"Failed to read file at: {filepath}") from error
        except psycopg.Error as error:
            logging.error(f"Failed to copy file to DB")
            raise RuntimeError(f"Failed to copy file to DB") from error

    @checkConnection
    async def copyFromIterableSQL(self, sql: Query, records: Iterable) -> None:
        try:
            async with AsyncClientCursor(self.aconn) as cursor:
                async with cursor.copy(sql) as copy:
                    for record in records:
                        await copy.write_row(record)
        except psycopg.Error as error:
            logging.error(f"Failed to copy iterable to DB")
            raise RuntimeError(f"Failed to copy iterable to DB") from error
