import os
import sqlite3
import logging
import tempfile
from hprint import hprint
from contextlib import closing
from typing import Iterable, Any


logger = logging.getLogger(__name__)


def sqlite3_connect(db_path=None) -> sqlite3.Connection:
    db_path = db_path or os.path.join(tempfile.gettempdir(), '__qqutils__.db')
    return sqlite3.connect(db_path)


def sqlite3_cursor(conn: sqlite3.Connection) -> sqlite3.Cursor:
    return conn.cursor()


def sqlite3_execute(sql: str, params: Iterable[Any] = None, *, db_path: str = None) -> None:
    db_path = db_path or os.path.join(tempfile.gettempdir(), '__qqutils__.db')
    # assert 'select' not in sql.lower(), 'Use sqlite3_query instead'
    logger.debug(f'[{db_path}] Executing [{sql}] with params {params}')
    with closing(sqlite3.connect(db_path)) as conn:
        with closing(conn.cursor()) as cursor:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
        conn.commit()


def sqlite3_query(sql: str, params: Iterable[Any] = None, *, db_path: str = None) -> list:
    db_path = db_path or os.path.join(tempfile.gettempdir(), '__qqutils__.db')
    assert 'select' in sql.lower(), 'Use sqlite3_execute instead'
    logger.debug(f'[{db_path}] Quering [{sql}] with params {params}')
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            if params:
                rows = cursor.execute(sql, params).fetchall()
            else:
                rows = cursor.execute(sql).fetchall()
            return [dict(row) for row in rows]


def sqlite3_select_all(table, db_path: str = None) -> dict:
    db_path = db_path or os.path.join(tempfile.gettempdir(), '__qqutils__.db')
    sql = f'select * from {table}'
    return sqlite3_query(sql, db_path=db_path)


def sqlite3_dump(table=None, db_path: str = None) -> dict:
    db_path = db_path or os.path.join(tempfile.gettempdir(), '__qqutils__.db')
    if table:
        sql = f'select * from {table}'
        rows = sqlite3_query(sql, db_path=db_path)
        rows0 = [{'TABLE': table, **row} for row in rows]
        hprint(rows0)
        print()
    else:
        for row in sqlite3_tables(db_path=db_path):
            table = row['name']
            sqlite3_dump(table, db_path=db_path)


def sqlite3_tables(db_path: str = None):
    db_path = db_path or os.path.join(tempfile.gettempdir(), '__qqutils__.db')
    sql = 'select name from sqlite_master where type = "table"'
    return sqlite3_query(sql, db_path=db_path)


def sqlite3_get(key: str, *, db_path: str = None, cast=str) -> Any:
    """Use SQLite to store key-value pairs"""
    db_path = db_path or os.path.join(tempfile.gettempdir(), '__qqutils__.db')
    sqlite3_execute('CREATE TABLE IF NOT EXISTS __cache__ (key TEXT PRIMARY KEY, value TEXT)', db_path=db_path)
    sql = 'select value from __cache__ where key = ?'
    records = sqlite3_query(sql, (key,))
    logger.debug(f'[{db_path}] Quering [{sql}] with params {key}, got {records}')
    return cast(records[-1]['value']) if records else None


def sqlite3_put(key: str, value: Any, *, db_path: str = None) -> str:
    """Use SQLite to store key-value pairs"""
    db_path = db_path or os.path.join(tempfile.gettempdir(), '__qqutils__.db')
    sqlite3_execute('CREATE TABLE IF NOT EXISTS __cache__ (key TEXT PRIMARY KEY, value TEXT)', db_path=db_path)

    q_sql = 'select value from __cache__ where key = ?'
    records = sqlite3_query(q_sql, (key,), db_path=db_path)

    if not records:
        u_sql = 'INSERT INTO __cache__ (key, value) VALUES (?, ?)'
        params = (key, value)
        ret = None
    else:
        u_sql = 'UPDATE __cache__ SET value = ? WHERE key = ?'
        params = (value, key)
        # print(records)
        ret = records[-1]['value']
    logger.debug(f'[{db_path}] Executing [{u_sql}] with params {params}')
    sqlite3_execute(u_sql, params, db_path=db_path)
    return ret
