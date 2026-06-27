"""
Database abstraction layer — Railway + SQLite safe
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SQLITE_PATH = os.environ.get(
    'SQLITE_PATH',
    os.path.join(BASE_DIR, 'geometry_home.db')
)

DATABASE_URL = os.environ.get('DATABASE_URL')

# fix postgres URL format
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

USE_PG = DATABASE_URL is not None and DATABASE_URL.strip() != ""


# -------------------------
# PostgreSQL import SAFELY
# -------------------------
if USE_PG:
    import psycopg2
    import psycopg2.extras


# -------------------------
# CONNECTION FACTORY
# -------------------------
def get_db():
    if USE_PG:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return PGConnection(conn)
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return SQLiteConnection(conn)


# -------------------------
# SQLITE WRAPPER
# -------------------------
class SQLiteConnection:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        return self._conn.execute(sql, params)

    def cursor(self):
        return self._conn.cursor()

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def __enter__(self): return self
    def __exit__(self, *a): self.close()


# -------------------------
# POSTGRES WRAPPER
# -------------------------
class PGConnection:
    def __init__(self, conn):
        self._conn = conn
        self._cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def execute(self, sql, params=()):
        self._cur.execute(sql, params)
        return self._cur

    def cursor(self):
        return self._cur

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def __enter__(self): return self
    def __exit__(self, *a): self.close()


# -------------------------
# HELPERS
# -------------------------
def last_insert_id(conn):
    if USE_PG:
        row = conn._cur.fetchone()
        return list(row.values())[0] if row else None
    else:
        return conn._conn.lastrowid


def returning_id(sql):
    if USE_PG:
        return sql + " RETURNING id"
    return sql
