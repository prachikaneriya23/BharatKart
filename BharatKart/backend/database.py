from contextlib import contextmanager
import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker
from utils.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
# Handle both postgres:// and postgresql:// prefixes for Aiven PostgreSQL with psycopg 3
if db_url.startswith("postgres://"):
    db_url = "postgresql+psycopg://" + db_url[len("postgres://"):]
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = "postgresql+psycopg://" + db_url[len("postgresql://"):]

is_sqlite = db_url.startswith("sqlite")
is_postgres = db_url.startswith("postgresql")

engine_kwargs = {"future": True, "pool_pre_ping": True}

if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
elif is_postgres:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_recycle"] = 300

try:
    engine = create_engine(db_url, **engine_kwargs)
    logger.info("SQLAlchemy engine initialized for: %s", "PostgreSQL" if is_postgres else "SQLite")
except Exception as exc:
    logger.warning("Failed to create engine with configured DATABASE_URL: %s. Falling back to local SQLite.", exc)
    db_url = "sqlite:///bharatkArt.db"
    is_sqlite = True
    is_postgres = False
    engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True, pool_pre_ping=True)

if is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()


@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database connection check failed: %s", exc)
        return False