import json
import logging
from typing import Optional
import uuid
from sqlalchemy import desc, select
from backend.database import get_db_session
from backend.models import City, OutboxEvent, Shop, User
from backend.schemas import ShopDTO, ShopRegistrationRequest
from services.auth_service import hash_password
from utils.helpers import generate_shop_code

logger = logging.getLogger(__name__)


class ShopRegistrationError(Exception):
    pass


def _mask_account(acc: str) -> str:
    if len(acc) <= 4:
        return acc
    return "•" * (len(acc) - 4) + acc[-4:]


def _to_shop_dto(shop: Shop, city: City) -> ShopDTO:
    return ShopDTO(
        id=shop.id,
        user_id=shop.user_id,
        shop_code=shop.shop_code,
        shop_name=shop.shop_name,
        owner_name=shop.owner_name,
        owner_email=shop.owner_email,
        owner_phone=shop.owner_phone,
        business_type=shop.business_type,
        primary_category=shop.primary_category,
        gstin=shop.gstin or "Unregistered / Exempted",
        pan_number=shop.pan_number,
        fssai_license=shop.fssai_license or "Not Applicable",
        city_id=city.id,
        city_name=f"{city.name}, {city.state}",
        shop_address=shop.shop_address,
        pincode=shop.pincode,
        pickup_slot=shop.pickup_slot,
        bank_account_holder=shop.bank_account_holder,
        bank_account_masked=_mask_account(shop.bank_account_number),
        bank_ifsc=shop.bank_ifsc,
        upi_id=shop.upi_id or "—",
        shop_description=shop.shop_description or "",
        status=shop.status,
        created_at=shop.created_at,
    )


def register_shop_atomic(req: ShopRegistrationRequest, user_id: Optional[int] = None) -> ShopDTO:
    try:
        with get_db_session() as session:
            city = session.execute(
                select(City).where(City.id == req.city_id, City.is_active.is_(True))
            ).scalar_one_or_none()
            if not city:
                raise ShopRegistrationError("Selected city hub is invalid or inactive.")

            duplicate = session.execute(
                select(Shop).where(Shop.shop_name.ilike(req.shop_name), Shop.city_id == city.id)
            ).scalar_one_or_none()
            if duplicate:
                raise ShopRegistrationError(
                    f"A shop named '{duplicate.shop_name}' is already registered in {city.name} (ID: {duplicate.shop_code})."
                )

            clean_email = req.owner_email.strip().lower()
            seller_user = None
            if user_id:
                seller_user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
            if not seller_user:
                seller_user = session.execute(select(User).where(User.email == clean_email)).scalar_one_or_none()

            if not seller_user:
                seller_user = User(
                    email=clean_email,
                    password_hash=hash_password(req.password or "Seller@123"),
                    role="seller",
                    full_name=req.owner_name,
                    phone=req.owner_phone,
                    is_active=True,
                )
                session.add(seller_user)
                session.flush()

            shop = Shop(
                user_id=seller_user.id,
                shop_code=generate_shop_code(),
                shop_name=req.shop_name,
                owner_name=req.owner_name,
                owner_email=clean_email,
                owner_phone=req.owner_phone,
                business_type=req.business_type,
                primary_category=req.primary_category,
                gstin=req.gstin.strip().upper() if req.gstin else None,
                pan_number=req.pan_number.strip().upper(),
                fssai_license=req.fssai_license.strip() if req.fssai_license else None,
                city_id=city.id,
                shop_address=req.shop_address,
                pincode=req.pincode,
                pickup_slot=req.pickup_slot,
                bank_account_holder=req.bank_account_holder,
                bank_account_number=req.bank_account_number,
                bank_ifsc=req.bank_ifsc.strip().upper(),
                upi_id=req.upi_id.strip() if req.upi_id else None,
                shop_description=req.shop_description.strip() if req.shop_description else None,
                status="PENDING",  # Awaiting admin approval
            )
            session.add(shop)
            session.flush()

            event_id = f"evt-{uuid.uuid4().hex}"
            payload = {
                "event_id": event_id,
                "event_type": "shop.created",
                "shop_id": shop.id,
                "shop_code": shop.shop_code,
                "shop_name": shop.shop_name,
                "owner_email": shop.owner_email,
                "city_id": city.id,
                "city_code": city.code,
                "primary_category": shop.primary_category,
                "status": shop.status,
            }
            session.add(
                OutboxEvent(
                    event_id=event_id,
                    aggregate_type="Shop",
                    aggregate_id=str(shop.id),
                    event_type="shop.created",
                    payload=json.dumps(payload),
                    status="PENDING",
                )
            )
            session.flush()
            return _to_shop_dto(shop, city)
    except ShopRegistrationError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error registering partner shop")
        raise ShopRegistrationError("Unable to complete shop registration right now. Please try again.") from exc


def approve_shop(shop_id: int) -> bool:
    """Admin action: approve seller shop and emit shop.approved Kafka outbox event."""
    with get_db_session() as session:
        shop = session.execute(select(Shop).where(Shop.id == shop_id)).scalar_one_or_none()
        if not shop:
            return False
        shop.status = "VERIFIED"

        from services.product_service import _seed_products_for_shop
        _seed_products_for_shop(session, shop.id)

        city = session.execute(select(City).where(City.id == shop.city_id)).scalar_one()
        event_id = f"evt-{uuid.uuid4().hex}"
        payload = {
            "event_id": event_id,
            "event_type": "shop.approved",
            "shop_id": shop.id,
            "shop_code": shop.shop_code,
            "shop_name": shop.shop_name,
            "city_code": city.code,
            "status": "VERIFIED",
        }
        session.add(
            OutboxEvent(
                event_id=event_id,
                aggregate_type="Shop",
                aggregate_id=str(shop.id),
                event_type="shop.approved",
                payload=json.dumps(payload),
                status="PENDING",
            )
        )
        session.flush()
        return True


def reject_shop(shop_id: int) -> bool:
    """Admin action: reject pending seller shop."""
    with get_db_session() as session:
        shop = session.execute(select(Shop).where(Shop.id == shop_id)).scalar_one_or_none()
        if not shop:
            return False
        shop.status = "REJECTED"
        session.flush()
        return True


def list_registered_shops(city_id: Optional[int] = None, status: Optional[str] = None) -> list[ShopDTO]:
    with get_db_session() as session:
        stmt = select(Shop, City).join(City, City.id == Shop.city_id).order_by(desc(Shop.created_at))
        if city_id is not None:
            stmt = stmt.where(Shop.city_id == city_id)
        if status is not None:
            stmt = stmt.where(Shop.status == status)
        rows = session.execute(stmt).all()
        return [_to_shop_dto(shop, city) for shop, city in rows]


def get_shop_by_id(shop_id: int) -> Optional[ShopDTO]:
    with get_db_session() as session:
        row = session.execute(
            select(Shop, City).join(City, City.id == Shop.city_id).where(Shop.id == shop_id)
        ).first()
        if not row:
            return None
        return _to_shop_dto(row[0], row[1])


def get_shop_by_code(shop_code: str) -> Optional[ShopDTO]:
    with get_db_session() as session:
        row = session.execute(
            select(Shop, City).join(City, City.id == Shop.city_id).where(Shop.shop_code == shop_code)
        ).first()
        if not row:
            return None
        return _to_shop_dto(row[0], row[1])


def get_shop_by_user_id(user_id: int) -> Optional[ShopDTO]:
    with get_db_session() as session:
        row = session.execute(
            select(Shop, City).join(City, City.id == Shop.city_id).where(Shop.user_id == user_id)
        ).first()
        if not row:
            return None
        return _to_shop_dto(row[0], row[1])
