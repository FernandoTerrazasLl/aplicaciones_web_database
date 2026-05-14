"""Consistency tests: verify that the SQLite → PostgreSQL migration preserved
all data correctly.

Run with:
    python -m pytest project/tests/check_consistency/ -v

Or standalone:
    python project/tests/check_consistency/test_check_consistency.py
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator, Tuple

import psycopg2
from psycopg2.extensions import connection as pg_connection, cursor as pg_cursor
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────
# Paths & DSN
# ──────────────────────────────────────────────────
SQLITE_DB_PATH: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'sqlite_to_postgres', 'db.sqlite',
)

DSN: dict[str, str | int] = {
    'dbname': os.environ.get('DB_NAME', 'movies_database'),
    'user': os.environ.get('DB_USER', 'app'),
    'password': os.environ.get('DB_PASSWORD', '123qwe'),
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'options': '-c search_path=public,content',
}

# Text fields that were coerced from NULL → '' during migration.
COERCED_TEXT_FIELDS: set[str] = {'description', 'file_path', 'certificate', 'role'}


# ──────────────────────────────────────────────────
# Connection helpers
# ──────────────────────────────────────────────────
@contextmanager
def open_connections() -> Generator[Tuple[sqlite3.Cursor, pg_cursor], None, None]:
    """Context manager that opens SQLite and PostgreSQL connections and yields
    their cursors.  Both connections are closed on exit."""
    sqlite_conn: sqlite3.Connection = sqlite3.connect(SQLITE_DB_PATH)
    pg_conn: pg_connection = psycopg2.connect(**DSN)
    try:
        yield sqlite_conn.cursor(), pg_conn.cursor()
    finally:
        sqlite_conn.close()
        pg_conn.close()


def _coerce_row(row: tuple, col_names: list[str]) -> tuple:
    """Apply the same NULL → '' coercion used during migration so SQLite and
    PostgreSQL values can be compared directly."""
    result: list = []
    for value, name in zip(row, col_names):
        if value is None and name in COERCED_TEXT_FIELDS:
            result.append('')
        else:
            result.append(str(value) if value is not None else None)
    return tuple(result)


# ──────────────────────────────────────────────────
# Count tests
# ──────────────────────────────────────────────────
def test_film_work_count(sqlite_cursor: sqlite3.Cursor, postgres_cursor: pg_cursor) -> None:
    sqlite_cursor.execute("SELECT COUNT(*) FROM film_work;")
    postgres_cursor.execute("SELECT COUNT(*) FROM content.film_work;")
    sqlite_count: int = sqlite_cursor.fetchone()[0]
    postgres_count: int = postgres_cursor.fetchone()[0]
    assert sqlite_count == postgres_count, (
        f"film_work count mismatch: SQLite={sqlite_count}, PG={postgres_count}"
    )


def test_genre_count(sqlite_cursor: sqlite3.Cursor, postgres_cursor: pg_cursor) -> None:
    sqlite_cursor.execute("SELECT COUNT(*) FROM genre;")
    postgres_cursor.execute("SELECT COUNT(*) FROM content.genre;")
    sqlite_count: int = sqlite_cursor.fetchone()[0]
    postgres_count: int = postgres_cursor.fetchone()[0]
    assert sqlite_count == postgres_count, (
        f"genre count mismatch: SQLite={sqlite_count}, PG={postgres_count}"
    )


def test_person_count(sqlite_cursor: sqlite3.Cursor, postgres_cursor: pg_cursor) -> None:
    sqlite_cursor.execute("SELECT COUNT(*) FROM person;")
    postgres_cursor.execute("SELECT COUNT(*) FROM content.person;")
    sqlite_count: int = sqlite_cursor.fetchone()[0]
    postgres_count: int = postgres_cursor.fetchone()[0]
    assert sqlite_count == postgres_count, (
        f"person count mismatch: SQLite={sqlite_count}, PG={postgres_count}"
    )


def test_genre_film_work_count(sqlite_cursor: sqlite3.Cursor, postgres_cursor: pg_cursor) -> None:
    sqlite_cursor.execute("SELECT COUNT(*) FROM genre_film_work;")
    postgres_cursor.execute("SELECT COUNT(*) FROM content.genre_film_work;")
    sqlite_count: int = sqlite_cursor.fetchone()[0]
    postgres_count: int = postgres_cursor.fetchone()[0]
    assert sqlite_count == postgres_count, (
        f"genre_film_work count mismatch: SQLite={sqlite_count}, PG={postgres_count}"
    )


def test_person_film_work_count(sqlite_cursor: sqlite3.Cursor, postgres_cursor: pg_cursor) -> None:
    sqlite_cursor.execute("SELECT COUNT(*) FROM person_film_work;")
    postgres_cursor.execute("SELECT COUNT(*) FROM content.person_film_work;")
    sqlite_count: int = sqlite_cursor.fetchone()[0]
    postgres_count: int = postgres_cursor.fetchone()[0]
    assert sqlite_count == postgres_count, (
        f"person_film_work count mismatch: SQLite={sqlite_count}, PG={postgres_count}"
    )


# ──────────────────────────────────────────────────
# Content consistency tests
# ──────────────────────────────────────────────────
def test_genre_consistency(sqlite_cursor: sqlite3.Cursor, postgres_cursor: pg_cursor) -> None:
    original_genres_batch: list[tuple] = sqlite_cursor.execute(
        "SELECT id, name, description FROM genre ORDER BY id;"
    ).fetchall()
    transferred_genres_batch: list[tuple] = postgres_cursor.execute(
        "SELECT id::text, name, description FROM content.genre ORDER BY id;"
    )
    transferred_genres_batch = postgres_cursor.fetchall()

    col_names: list[str] = ['id', 'name', 'description']
    original_normalized: list[tuple] = [_coerce_row(r, col_names) for r in original_genres_batch]
    transferred_normalized: list[tuple] = [_coerce_row(r, col_names) for r in transferred_genres_batch]

    assert len(original_normalized) == len(transferred_normalized)
    assert original_normalized == transferred_normalized


def test_film_work_content(sqlite_cursor: sqlite3.Cursor, postgres_cursor: pg_cursor) -> None:
    original_film_work_batch: list[tuple] = sqlite_cursor.execute(
        "SELECT id, title, description, creation_date, rating, type FROM film_work ORDER BY id;"
    ).fetchall()
    postgres_cursor.execute(
        "SELECT id::text, title, description, creation_date::text, rating, type "
        "FROM content.film_work ORDER BY id;"
    )
    transferred_film_work_batch: list[tuple] = postgres_cursor.fetchall()

    col_names: list[str] = ['id', 'title', 'description', 'creation_date', 'rating', 'type']
    original_normalized: list[tuple] = [_coerce_row(r, col_names) for r in original_film_work_batch]
    transferred_normalized: list[tuple] = [_coerce_row(r, col_names) for r in transferred_film_work_batch]

    assert len(original_normalized) == len(transferred_normalized)
    assert original_normalized == transferred_normalized


def test_person_consistency(sqlite_cursor: sqlite3.Cursor, postgres_cursor: pg_cursor) -> None:
    original_persons_batch: list[tuple] = sqlite_cursor.execute(
        "SELECT id, full_name FROM person ORDER BY id;"
    ).fetchall()
    postgres_cursor.execute(
        "SELECT id::text, full_name FROM content.person ORDER BY id;"
    )
    transferred_persons_batch: list[tuple] = postgres_cursor.fetchall()

    col_names: list[str] = ['id', 'full_name']
    original_normalized: list[tuple] = [_coerce_row(r, col_names) for r in original_persons_batch]
    transferred_normalized: list[tuple] = [_coerce_row(r, col_names) for r in transferred_persons_batch]

    assert len(original_normalized) == len(transferred_normalized)
    assert original_normalized == transferred_normalized


def test_genre_film_work_consistency(sqlite_cursor: sqlite3.Cursor, postgres_cursor: pg_cursor) -> None:
    original_relations_batch: list[tuple] = sqlite_cursor.execute(
        "SELECT id, genre_id, film_work_id FROM genre_film_work ORDER BY id;"
    ).fetchall()
    postgres_cursor.execute(
        "SELECT id::text, genre_id::text, film_work_id::text FROM content.genre_film_work ORDER BY id;"
    )
    transferred_relations_batch: list[tuple] = postgres_cursor.fetchall()

    col_names: list[str] = ['id', 'genre_id', 'film_work_id']
    original_normalized: list[tuple] = [_coerce_row(r, col_names) for r in original_relations_batch]
    transferred_normalized: list[tuple] = [_coerce_row(r, col_names) for r in transferred_relations_batch]

    assert len(original_normalized) == len(transferred_normalized)
    assert original_normalized == transferred_normalized


def test_person_film_work_consistency(sqlite_cursor: sqlite3.Cursor, postgres_cursor: pg_cursor) -> None:
    original_relations_batch: list[tuple] = sqlite_cursor.execute(
        "SELECT id, person_id, film_work_id, role FROM person_film_work ORDER BY id;"
    ).fetchall()
    postgres_cursor.execute(
        "SELECT id::text, person_id::text, film_work_id::text, role "
        "FROM content.person_film_work ORDER BY id;"
    )
    transferred_relations_batch: list[tuple] = postgres_cursor.fetchall()

    col_names: list[str] = ['id', 'person_id', 'film_work_id', 'role']
    original_normalized: list[tuple] = [_coerce_row(r, col_names) for r in original_relations_batch]
    transferred_normalized: list[tuple] = [_coerce_row(r, col_names) for r in transferred_relations_batch]

    assert len(original_normalized) == len(transferred_normalized)
    assert original_normalized == transferred_normalized


# ──────────────────────────────────────────────────
# Main — run all tests
# ──────────────────────────────────────────────────
if __name__ == '__main__':
    all_tests = [
        test_film_work_count,
        test_genre_count,
        test_person_count,
        test_genre_film_work_count,
        test_person_film_work_count,
        test_genre_consistency,
        test_film_work_content,
        test_person_consistency,
        test_genre_film_work_consistency,
        test_person_film_work_consistency,
    ]

    with open_connections() as (sqlite_cursor, postgres_cursor):
        passed: int = 0
        failed: int = 0
        for test_fn in all_tests:
            try:
                test_fn(sqlite_cursor, postgres_cursor)
                print(f"  ✅ {test_fn.__name__}")
                passed += 1
            except AssertionError as e:
                print(f"  ❌ {test_fn.__name__}: {e}")
                failed += 1

    print(f"\nResults: {passed} passed, {failed} failed out of {passed + failed} tests.")
    if failed > 0:
        exit(1)
