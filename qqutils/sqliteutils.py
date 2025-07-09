import os
import json
import sqlite3
import logging
import tempfile
from typing import List
from hprint import hprint
from contextlib import closing
from typing import Iterable, Any, Optional, Dict
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import sessionmaker, Session
import getpass

__all__ = (
    'sqlite3_connect',
    'sqlite3_cursor',
    'sqlite3_execute',
    'sqlite3_query',
    'sqlite3_tables',
    'sqlite3_select_all',
    'sqlite3_dump',
    'sqlite3_get',
    'sqlite3_delete',
    'sqlite3_put',
    'sqlite3_jget',
    'sqlite3_jget_all',
    'sqlite3_jput',
    'sqlalchemy_get_engine',
    'sqlalchemy_get_session',
    'sqlalchemy_execute',
)

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = os.path.join(tempfile.gettempdir(), f'__qqutils_{os.getenv("SUDO_USER") or getpass.getuser()}__.db')


def _ensure_cache_table(db_path) -> None:
    sqlite3_execute('CREATE TABLE IF NOT EXISTS __cache__ (key TEXT PRIMARY KEY, value TEXT, data JSON)', db_path=db_path)


def sqlite3_connect(db_path=None) -> sqlite3.Connection:
    db_path = db_path or _DEFAULT_DB_PATH
    return sqlite3.connect(db_path)


def sqlite3_cursor(conn: sqlite3.Connection) -> sqlite3.Cursor:
    return conn.cursor()


def sqlite3_execute(sql: str, params: Iterable[Any] = None, *, db_path: str = None) -> None:
    db_path = db_path or _DEFAULT_DB_PATH
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
    db_path = db_path or _DEFAULT_DB_PATH
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
    db_path = db_path or _DEFAULT_DB_PATH
    sql = f'select * from "{table}"'
    return sqlite3_query(sql, db_path=db_path)


def sqlite3_dump(table=None, db_path: str = None) -> dict:
    if table:
        sql = f'select * from "{table}"'
        rows = sqlite3_query(sql, db_path=db_path)
        rows0 = [{'TABLE': table, **row} for row in rows]
        hprint(rows0)
        print()
    else:
        for row in sqlite3_tables(db_path=db_path):
            table = row['name']
            sqlite3_dump(table, db_path=db_path)


def sqlite3_tables(db_path: str = None):
    sql = 'select name from sqlite_master where type = "table"'
    return sqlite3_query(sql, db_path=db_path)


def sqlite3_get(key: str, *, db_path: str = None, cast=str) -> Any:
    """Use SQLite to store key-value pairs"""
    _ensure_cache_table(db_path)
    sql = 'select value from __cache__ where key = ?'
    records = sqlite3_query(sql, (key,), db_path=db_path)
    logger.debug(f'[{db_path}] Quering [{sql}] with params {key}, got {records}')
    return cast(records[-1]['value']) if records else None


def sqlite3_delete(key: str, *, db_path: str = None) -> None:
    """Use SQLite to delete a key-value pair"""
    _ensure_cache_table(db_path)
    del_sql = 'DELETE FROM __cache__ WHERE key = ?'
    logger.debug(f'[{db_path}] Executing [{del_sql}] with params {key}')
    sqlite3_execute(del_sql, (key,), db_path=db_path)


def sqlite3_put(key: str, value: Any, *, db_path: str = None) -> str:
    """Use SQLite to store key-value pairs"""
    _ensure_cache_table(db_path)

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


def sqlite3_jget(key: str, *, db_path: str = None) -> Optional[dict]:
    """Use SQLite to fetch key-value pairs by key as JSON"""
    _ensure_cache_table(db_path)
    sql = 'select data from __cache__ where key = ?'
    records = sqlite3_query(sql, (key,), db_path=db_path)
    logger.debug(f'[{db_path}] Quering [{sql}] with params {key}, got {records}')
    return json.loads(records[-1]['data']) if records else None


def sqlite3_jget_all(db_path: str = None) -> List[Dict]:
    """Use SQLite to fetch all key-value pairs as JSON"""
    _ensure_cache_table(db_path)
    sql = 'select * from __cache__'
    records = sqlite3_query(sql, None, db_path=db_path)
    logger.debug(f'[{db_path}] Quering [{sql}], got {len(records)} records')
    return records


def sqlite3_jput(key: str, data: dict, *, db_path: str = None) -> Optional[dict]:
    """Use SQLite to store key-value pairs as JSON"""
    _ensure_cache_table(db_path)

    q_sql = 'select data from __cache__ where key = ?'
    records = sqlite3_query(q_sql, (key,), db_path=db_path)

    if not records:
        u_sql = 'INSERT INTO __cache__ (key, data) VALUES (?, ?)'
        params = (key, json.dumps(data))
        ret = None
    else:
        u_sql = 'UPDATE __cache__ SET data = ? WHERE key = ?'
        params = (json.dumps(data), key)
        # print(records)
        ret = json.loads(records[-1]['data'])
    logger.debug(f'[{db_path}] Executing [{u_sql}] with params {params}')
    sqlite3_execute(u_sql, params, db_path=db_path)
    return ret


# SQLAlchemy

def sqlalchemy_get_engine(db_path: str = None) -> Engine:
    db_path = db_path or _DEFAULT_DB_PATH
    return create_engine(
        f'sqlite:///{db_path}?check_same_thread=False',
        echo=logger.isEnabledFor(logging.DEBUG)
    )


def sqlalchemy_get_session(engine: Engine) -> Session:
    return sessionmaker(bind=engine)()


def sqlalchemy_execute(sql: str, engine: Engine, params: dict = None) -> List[dict]:
    logger.debug(f'[{engine.url}] Executing [{sql}] with params {params}')
    session = sqlalchemy_get_session(engine)
    sql = text(sql)
    if params:
        rows = session.execute(sql, params).fetchall()
    else:
        rows = session.execute(sql).fetchall()
    return rows
