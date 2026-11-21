import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Load environment variables from BharatKart/.env and root .env
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv()

DEFAULT_DB_PATH = (BASE_DIR / "bharatkArt.db").resolve().as_posix()
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_DB_PATH}"


def _resolve_ca_path(path_str: str) -> str:
    if not path_str:
        return ""
    p = Path(path_str)
    if p.is_absolute() and p.exists():
        return str(p)
    # Check relative to BASE_DIR.parent (workspace root)
    p_root = BASE_DIR.parent / path_str
    if p_root.exists():
        return str(p_root)
    # Check relative to BASE_DIR
    p_base = BASE_DIR / path_str
    if p_base.exists():
        return str(p_base)
    return path_str


@dataclass(frozen=True)
class Settings:
    APP_NAME: str = "BharatKart"
    DATABASE_URL: str = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
    KAFKA_USERNAME: str = os.getenv("KAFKA_USERNAME", os.getenv("KAFKA_SASL_USERNAME", ""))
    KAFKA_PASSWORD: str = os.getenv("KAFKA_PASSWORD", os.getenv("KAFKA_SASL_PASSWORD", ""))
    KAFKA_SECURITY_PROTOCOL: str = os.getenv("KAFKA_SECURITY_PROTOCOL", "SASL_SSL" if os.getenv("KAFKA_USERNAME") else "PLAINTEXT")
    KAFKA_SASL_MECHANISM: str = os.getenv("KAFKA_SASL_MECHANISM", "SCRAM-SHA-256")
    KAFKA_TOPIC_PREFIX: str = os.getenv("KAFKA_TOPIC_PREFIX", "bharatkart.")
    KAFKA_CONSUMER_GROUP: str = os.getenv("KAFKA_CONSUMER_GROUP", "bharatkart-consumer-group")
    KAFKA_CA_LOCATION: str = _resolve_ca_path(os.getenv("KAFKA_CA_LOCATION", "certificates/kafka-ca.pem"))

    # OpenSearch Configuration
    OPENSEARCH_HOST: str = os.getenv("OPENSEARCH_HOST", os.getenv("OPENSEARCH_URL", ""))
    OPENSEARCH_URL: str = os.getenv("OPENSEARCH_URL", os.getenv("OPENSEARCH_HOST", ""))
    OPENSEARCH_USERNAME: str = os.getenv("OPENSEARCH_USERNAME", "")
    OPENSEARCH_PASSWORD: str = os.getenv("OPENSEARCH_PASSWORD", "")
    OPENSEARCH_USE_SSL: bool = os.getenv("OPENSEARCH_USE_SSL", "true").lower() == "true"
    OPENSEARCH_VERIFY_CERTS: bool = os.getenv("OPENSEARCH_VERIFY_CERTS", "true").lower() == "true"

    # AI / LLM
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Business Rules & Thresholds
    FREE_SHIPPING_THRESHOLD: float = float(os.getenv("FREE_SHIPPING_THRESHOLD", "499.00"))
    STANDARD_SHIPPING_FEE: float = float(os.getenv("STANDARD_SHIPPING_FEE", "49.00"))
    LOW_STOCK_THRESHOLD: int = int(os.getenv("LOW_STOCK_THRESHOLD", "5"))
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "bharatkart-secure-secret-key-2026")


settings = Settings()
