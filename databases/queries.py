import sqlite3
import os
import tempfile
from contextlib import closing
from pathlib import Path

PRIMARY_DB_PATH = Path(os.getenv("DB_PATH", "databases/shop_data.db"))
FALLBACK_DB_PATH = Path(tempfile.gettempdir()) / "haski_client_shop_data.db"
ACTIVE_DB_PATH: Path | None = None
_products_cache = None

def connect() -> sqlite3.Connection:
    global ACTIVE_DB_PATH

    if ACTIVE_DB_PATH is None:
        for candidate in (PRIMARY_DB_PATH, FALLBACK_DB_PATH):
            candidate.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(candidate))
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("ROLLBACK")
                ACTIVE_DB_PATH = candidate
                conn.close()
                break
            except sqlite3.OperationalError:
                conn.close()
        else:
            raise sqlite3.OperationalError("Unable to open writable database path")

    conn = sqlite3.connect(str(ACTIVE_DB_PATH))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=OFF")
    except sqlite3.OperationalError:
        # Some cloud-sync folders may block PRAGMA changes on a locked DB file.
        # In that case we continue with default SQLite settings.
        pass
    return conn


def create_tables() -> None:
    with closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                description TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                admin_response TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                answered_at TEXT
            )
            """
        )
        conn.commit()


def add_user(user_id: int, username: str | None, full_name: str | None) -> None:
    with closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
            """,
            (user_id, username, full_name),
        )
        conn.commit()


def get_all_user_ids() -> list[int]:
    with closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        rows = cursor.fetchall()
    return [row[0] for row in rows]


def add_product(name: str, price: int, description: str) -> None:
    global _products_cache
    _products_cache = None
    with closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
            (name, price, description),
        )
        conn.commit()


def get_products() -> list[tuple[int, str]]:
    with closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name FROM products WHERE is_active=1 ORDER BY id DESC"
        )
        products = cursor.fetchall()
    return products


def get_products_for_user() -> list[tuple[int, str, int]]:
    global _products_cache

    if _products_cache is not None:
        return _products_cache

    with closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, price FROM products WHERE is_active=1 ORDER BY id DESC"
        )
        _products_cache = cursor.fetchall()

    return _products_cache


def get_product(product_id: int) -> tuple[str, int, str] | None:
    with closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name, price, description
            FROM products
            WHERE id=? AND is_active=1
            """,
            (product_id,),
        )
        product = cursor.fetchone()
    return product


def delete_product(product_id: int) -> bool:
    global _products_cache
    _products_cache = None
    with closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
        return cursor.rowcount > 0


def update_product_price(product_id: int, price: int) -> bool:
    global _products_cache
    _products_cache = None
    with closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE products SET price=? WHERE id=?",
            (price, product_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def add_support_ticket(
    user_id: int,
    username: str | None,
    full_name: str | None,
    message: str,
) -> int:
    with closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO support_tickets (user_id, username, full_name, message)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, username, full_name, message),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_open_support_ticket_ids() -> list[int]:
    with closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id
            FROM support_tickets
            WHERE status='open'
            ORDER BY id ASC
            """
        )
        rows = cursor.fetchall()
    return [row[0] for row in rows]


def get_support_ticket(
    ticket_id: int,
) -> tuple[int, int, str | None, str | None, str, str, str] | None:
    with closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, user_id, username, full_name, message, status, created_at
            FROM support_tickets
            WHERE id=?
            """,
            (ticket_id,),
        )
        row = cursor.fetchone()
    return row


def ignore_support_ticket(ticket_id: int) -> bool:
    with closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE support_tickets
            SET status='ignored'
            WHERE id=? AND status='open'
            """,
            (ticket_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


def answer_support_ticket(ticket_id: int, admin_response: str) -> bool:
    with closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE support_tickets
            SET status='answered',
                admin_response=?,
                answered_at=CURRENT_TIMESTAMP
            WHERE id=? AND status='open'
            """,
            (admin_response, ticket_id),
        )
        conn.commit()
        return cursor.rowcount > 0
