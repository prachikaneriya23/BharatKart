import hashlib
import logging
import os
import secrets
from typing import Optional
from sqlalchemy import select
from backend.database import get_db_session
from backend.models import Customer, Shop, User
from backend.schemas import UserDTO

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash password securely using PBKDF2 with SHA-256 and unique 16-byte salt."""
    salt = secrets.token_hex(16)
    iterations = 100_000
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    try:
        if not hashed_password or "$" not in hashed_password:
            return False
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            # If generated via Werkzeug format
            try:
                from werkzeug.security import check_password_hash
                return check_password_hash(hashed_password, plain_password)
            except Exception:
                return False
        _, iterations_str, salt, expected_hex = parts
        iterations = int(iterations_str)
        key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return secrets.compare_digest(key.hex(), expected_hex)
    except Exception as exc:
        logger.error("Password verification error: %s", exc)
        return False


def get_user_dto(user: User, shop: Optional[Shop] = None) -> UserDTO:
    return UserDTO(
        id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        phone=user.phone,
        is_active=user.is_active,
        shop_id=shop.id if shop else None,
        shop_code=shop.shop_code if shop else None,
    )


def authenticate_user(email: str, password: str) -> Optional[UserDTO]:
    """Authenticate user with email and password, returning UserDTO with attached shop if seller."""
    with get_db_session() as session:
        user = session.execute(
            select(User).where(User.email == email.strip().lower(), User.is_active.is_(True))
        ).scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None

        shop = None
        if user.role == "seller":
            shop = session.execute(select(Shop).where(Shop.user_id == user.id)).scalar_one_or_none()
            if not shop:
                shop = session.execute(select(Shop).where(Shop.owner_email == user.email)).scalar_one_or_none()

        return get_user_dto(user, shop)


def create_user(
    email: str,
    password: str,
    full_name: str,
    phone: Optional[str] = None,
    role: str = "customer",
) -> UserDTO:
    """Create a new user with hashed password and role."""
    clean_email = email.strip().lower()
    with get_db_session() as session:
        existing = session.execute(select(User).where(User.email == clean_email)).scalar_one_or_none()
        if existing:
            raise ValueError(f"User with email '{clean_email}' already exists.")

        user = User(
            email=clean_email,
            password_hash=hash_password(password),
            role=role,
            full_name=full_name.strip(),
            phone=phone.strip() if phone else None,
            is_active=True,
        )
        session.add(user)
        session.flush()
        return get_user_dto(user)


def get_user_by_id(user_id: int) -> Optional[UserDTO]:
    with get_db_session() as session:
        user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            return None
        shop = None
        if user.role == "seller":
            shop = session.execute(select(Shop).where(Shop.user_id == user.id)).scalar_one_or_none()
        return get_user_dto(user, shop)
