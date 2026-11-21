import logging
from sqlalchemy import text
from backend.database import Base, engine, get_db_session, is_sqlite
from backend import models  # noqa: F401
from database.seed_data import seed_initial_data

logger = logging.getLogger(__name__)


def _run_migrations(connection) -> None:
    """Safe, idempotent column additions for existing SQLite/PostgreSQL schemas."""
    alter_statements = [
        # Table, Column, Type
        ("products", "shop_id", "INTEGER REFERENCES shops(id)"),
        ("order_items", "suborder_id", "INTEGER REFERENCES suborders(id)"),
        ("order_items", "shop_id", "INTEGER REFERENCES shops(id)"),
        ("order_items", "variant_info", "VARCHAR(100)"),
        ("orders", "customer_id", "INTEGER REFERENCES customers(id)"),
        ("shops", "user_id", "INTEGER REFERENCES users(id)"),
        ("customers", "user_id", "INTEGER REFERENCES users(id)"),
        ("inventories", "shop_id", "INTEGER REFERENCES shops(id)"),
    ]

    for table, col, col_type in alter_statements:
        try:
            if is_sqlite:
                cursor = connection.execute(text(f"PRAGMA table_info({table})"))
                columns = [row[1] for row in cursor.fetchall()]
                if col not in columns:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                    logger.info("Migrated table '%s': added column '%s'.", table, col)
            else:
                # PostgreSQL information_schema check
                cursor = connection.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = :tbl AND column_name = :col"
                    ),
                    {"tbl": table, "col": col},
                )
                if not cursor.fetchone():
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                    logger.info("Migrated table '%s': added column '%s'.", table, col)
        except Exception as exc:
            # Ignore if table doesn't exist yet or column already exists
            logger.debug("Migration check for %s.%s skipped or already present: %s", table, col, exc)


def initialize_database() -> None:
    """Create all schema tables, perform idempotent column migrations, and seed initial demo data."""
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        _run_migrations(conn)

    with get_db_session() as session:
        seed_initial_data(session)
    logger.info("Database initialized and verified successfully.")
