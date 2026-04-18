from __future__ import annotations

import time
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from .settings import settings
from .sql_guard import validate_readonly_sql


class BridgeDbError(RuntimeError):
    pass


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    duration_ms: int
    sql_hash: str
    applied_limit: int


class DatabaseClient:
    def __init__(self) -> None:
        self._conn_kwargs = {
            "host": settings.db_host,
            "port": settings.db_port,
            "user": settings.db_user,
            "password": settings.db_password,
            "database": settings.db_name,
            "cursorclass": DictCursor,
            "autocommit": False,
            "charset": "utf8mb4",
        }

    def _connect(self):
        if not settings.db_name or not settings.db_user:
            raise BridgeDbError("Database settings are incomplete")
        return pymysql.connect(**self._conn_kwargs)

    def health_check(self) -> dict[str, Any]:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS ok")
                row = cur.fetchone() or {}
                return {"db_ok": bool(row.get("ok", 0))}
        finally:
            conn.close()

    def list_tables(self) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name, table_type
                    FROM information_schema.tables
                    WHERE table_schema = %s
                    ORDER BY table_name
                    """,
                    (settings.db_name,),
                )
                return list(cur.fetchall())
        finally:
            conn.close()

    def describe_table(self, table_name: str) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT column_name, data_type, is_nullable, column_key, column_default
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                    """,
                    (settings.db_name, table_name),
                )
                return list(cur.fetchall())
        finally:
            conn.close()

    def run_sql_readonly(
        self, sql: str, params: dict[str, Any] | list[Any] | None = None, limit: int | None = None
    ) -> QueryResult:
        validated_sql = validate_readonly_sql(sql)

        effective_limit = settings.max_rows
        if isinstance(limit, int) and limit > 0:
            effective_limit = min(limit, settings.max_rows)

        sql_hash = sha256(validated_sql.encode("utf-8")).hexdigest()

        conn = self._connect()
        started = time.monotonic()
        try:
            with conn.cursor() as cur:
                timeout_seconds = max(1, int(settings.query_timeout_ms / 1000))
                try:
                    cur.execute("SET SESSION max_statement_time = %s", (timeout_seconds,))
                except Exception:
                    pass

                cur.execute("SET SESSION TRANSACTION READ ONLY")
                cur.execute("SET SESSION sql_select_limit = %s", (effective_limit,))
                cur.execute("START TRANSACTION READ ONLY")

                if params is None:
                    cur.execute(validated_sql)
                else:
                    cur.execute(validated_sql, params)

                rows = list(cur.fetchall())
                conn.rollback()

                columns = list(rows[0].keys()) if rows else []
                return QueryResult(
                    columns=columns,
                    rows=rows,
                    row_count=len(rows),
                    duration_ms=int((time.monotonic() - started) * 1000),
                    sql_hash=sql_hash,
                    applied_limit=effective_limit,
                )
        except Exception as exc:
            conn.rollback()
            raise BridgeDbError(str(exc)) from exc
        finally:
            conn.close()
