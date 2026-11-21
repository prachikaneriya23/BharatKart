import logging
from typing import Optional
from sqlalchemy import select
from backend.database import get_db_session
from backend.models import City, Customer, User
from backend.schemas import CustomerDTO, CustomerRegistrationRequest
from services.auth_service import hash_password

logger = logging.getLogger(__name__)


class CustomerRegistrationError(Exception):
    pass


def register_or_update_customer(req: CustomerRegistrationRequest, user_id: Optional[int] = None) -> CustomerDTO:
    try:
        with get_db_session() as session:
            city = session.execute(
                select(City).where(City.id == req.default_city_id, City.is_active.is_(True))
            ).scalar_one_or_none()
            if not city:
                raise CustomerRegistrationError("Selected default city is invalid or inactive.")

            clean_email = req.email.strip().lower()

            # Ensure user account exists
            user = None
            if user_id:
                user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
            if not user:
                user = session.execute(select(User).where(User.email == clean_email)).scalar_one_or_none()

            if not user:
                user = User(
                    email=clean_email,
                    password_hash=hash_password(req.password or "Bharat@123"),
                    role="customer",
                    full_name=req.full_name,
                    phone=req.phone,
                    is_active=True,
                )
                session.add(user)
                session.flush()

            existing = session.execute(select(Customer).where(Customer.email == clean_email)).scalar_one_or_none()
            if existing:
                existing.full_name = req.full_name
                existing.phone = req.phone
                existing.default_city_id = city.id
                existing.default_address = req.default_address
                existing.pincode = req.pincode
                existing.user_id = user.id
                customer = existing
            else:
                customer = Customer(
                    user_id=user.id,
                    full_name=req.full_name,
                    email=clean_email,
                    phone=req.phone,
                    default_city_id=city.id,
                    default_address=req.default_address,
                    pincode=req.pincode,
                )
                session.add(customer)

            session.flush()
            return CustomerDTO(
                id=customer.id,
                user_id=customer.user_id,
                full_name=customer.full_name,
                email=customer.email,
                phone=customer.phone,
                default_city_id=city.id,
                city_name=f"{city.name}, {city.state}",
                default_address=customer.default_address,
                pincode=customer.pincode,
            )
    except CustomerRegistrationError:
        raise
    except Exception as exc:
        logger.exception("Error registering customer")
        raise CustomerRegistrationError("Unable to save customer profile right now.") from exc


def get_customer_by_email(email: str) -> Optional[CustomerDTO]:
    with get_db_session() as session:
        cust = session.execute(
            select(Customer, City)
            .join(City, City.id == Customer.default_city_id)
            .where(Customer.email == email.strip().lower())
        ).first()
        if not cust:
            return None
        c, city = cust
        return CustomerDTO(
            id=c.id,
            user_id=c.user_id,
            full_name=c.full_name,
            email=c.email,
            phone=c.phone,
            default_city_id=city.id,
            city_name=f"{city.name}, {city.state}",
            default_address=c.default_address,
            pincode=c.pincode,
        )


def get_customer_by_user_id(user_id: int) -> Optional[CustomerDTO]:
    with get_db_session() as session:
        cust = session.execute(
            select(Customer, City)
            .join(City, City.id == Customer.default_city_id)
            .where(Customer.user_id == user_id)
        ).first()
        if not cust:
            return None
        c, city = cust
        return CustomerDTO(
            id=c.id,
            user_id=c.user_id,
            full_name=c.full_name,
            email=c.email,
            phone=c.phone,
            default_city_id=city.id,
            city_name=f"{city.name}, {city.state}",
            default_address=c.default_address,
            pincode=c.pincode,
        )
