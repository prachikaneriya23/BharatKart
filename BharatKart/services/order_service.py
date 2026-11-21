from decimal import Decimal
import json
import logging
from typing import List, Optional
import uuid
from sqlalchemy import desc, func, select, update
from backend.database import get_db_session, is_postgres, is_sqlite
from backend.models import (
    City,
    Customer,
    Inventory,
    Order,
    OrderItem,
    OutboxEvent,
    Product,
    Shop,
    SubOrder,
)
from backend.schemas import (
    CheckoutRequest,
    OrderConfirmationDTO,
    OrderItemDTO,
    SubOrderDTO,
)
from utils.config import settings
from utils.helpers import generate_order_number

logger = logging.getLogger(__name__)


class OrderProcessingError(Exception):
    pass


def calculate_totals(subtotal: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    subtotal = Decimal(subtotal).quantize(Decimal("0.01"))
    if subtotal <= Decimal("0.00"):
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00")
    shipping = (
        Decimal("0.00")
        if subtotal >= Decimal(str(settings.FREE_SHIPPING_THRESHOLD))
        else Decimal(str(settings.STANDARD_SHIPPING_FEE)).quantize(Decimal("0.01"))
    )
    total = (subtotal + shipping).quantize(Decimal("0.01"))
    return subtotal, shipping, total


def _build_order_dto(session, order: Order) -> OrderConfirmationDTO:
    city = session.execute(select(City).where(City.id == order.city_id)).scalar_one()
    items = session.execute(
        select(OrderItem, Product, Shop)
        .join(Product, Product.id == OrderItem.product_id)
        .outerjoin(Shop, Shop.id == OrderItem.shop_id)
        .where(OrderItem.order_id == order.id)
    ).all()

    item_dtos = [
        OrderItemDTO(
            product_id=item.product_id,
            product_name=item.product_name,
            variant_info=item.variant_info,
            unit_price=Decimal(item.unit_price),
            quantity=item.quantity,
            line_total=Decimal(item.line_total),
            shop_id=shop.id if shop else item.shop_id,
            shop_name=shop.shop_name if shop else None,
        )
        for item, prod, shop in items
    ]

    suborders = session.execute(
        select(SubOrder, Shop).join(Shop, Shop.id == SubOrder.shop_id).where(SubOrder.parent_order_id == order.id)
    ).all()

    suborder_dtos = []
    for sub, shop in suborders:
        sub_items = [i for i in item_dtos if i.shop_id == shop.id]
        suborder_dtos.append(
            SubOrderDTO(
                id=sub.id,
                suborder_number=sub.suborder_number,
                shop_id=shop.id,
                shop_name=shop.shop_name,
                shop_code=shop.shop_code,
                subtotal=Decimal(sub.subtotal),
                status=sub.status,
                created_at=sub.created_at,
                items=sub_items,
            )
        )

    outbox = session.execute(
        select(OutboxEvent).where(OutboxEvent.aggregate_type == "Order", OutboxEvent.aggregate_id == str(order.id))
    ).scalar_one_or_none()

    return OrderConfirmationDTO(
        order_id=order.id,
        order_number=order.order_number,
        city_name=f"{city.name}, {city.state}",
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        customer_phone=order.customer_phone,
        shipping_address=order.shipping_address,
        pincode=order.pincode,
        subtotal_amount=Decimal(order.subtotal),
        shipping_fee=Decimal(order.shipping_fee),
        total_amount=Decimal(order.total),
        status=order.status,
        created_at=order.created_at,
        items=item_dtos,
        suborders=suborder_dtos,
        outbox_event_id=outbox.event_id if outbox else None,
    )


def place_order_atomic(req: CheckoutRequest) -> OrderConfirmationDTO:
    """Atomic multi-store checkout. Deducts inventory per store and creates parent order + shop suborders."""
    if not req.items:
        raise OrderProcessingError("Your shopping cart is empty.")

    requested_map: dict[int, int] = {}
    item_variant_map: dict[int, Optional[str]] = {}
    for item in req.items:
        requested_map[item.product_id] = requested_map.get(item.product_id, 0) + item.quantity
        if item.variant_info:
            item_variant_map[item.product_id] = item.variant_info

    try:
        with get_db_session() as session:
            existing_order = session.execute(
                select(Order).where(Order.idempotency_key == req.idempotency_key)
            ).scalar_one_or_none()
            if existing_order:
                return _build_order_dto(session, existing_order)

            city = session.execute(
                select(City).where(City.id == req.city_id, City.is_active.is_(True))
            ).scalar_one_or_none()
            if not city:
                raise OrderProcessingError("Selected delivery city is invalid or inactive.")

            product_ids = sorted(requested_map.keys())
            inv_stmt = select(Inventory).where(Inventory.city_id == city.id, Inventory.product_id.in_(product_ids))
            if is_postgres:
                inv_stmt = inv_stmt.with_for_update()

            inventories = session.execute(inv_stmt).scalars().all()
            inv_by_pid = {inv.product_id: inv for inv in inventories}
            products = session.execute(
                select(Product, Shop).outerjoin(Shop, Shop.id == Product.shop_id).where(Product.id.in_(product_ids))
            ).all()
            prod_lookup = {p.id: (p, s) for p, s in products}

            subtotal = Decimal("0.00")
            line_records: list[dict] = []
            shop_items_map: dict[int, list[dict]] = {}

            for pid in product_ids:
                qty = requested_map[pid]
                if pid not in prod_lookup or pid not in inv_by_pid:
                    raise OrderProcessingError(f"Product ID {pid} is not available in {city.name}.")
                prod, shop = prod_lookup[pid]
                inv = inv_by_pid[pid]

                if inv.stock_quantity < qty:
                    raise OrderProcessingError(
                        f"Insufficient stock for '{prod.name}' in {city.name} (Requested: {qty}, Available: {inv.stock_quantity})."
                    )

                unit_price = Decimal(prod.price).quantize(Decimal("0.01"))
                line_total = (unit_price * qty).quantize(Decimal("0.01"))
                subtotal += line_total

                shop_id = shop.id if shop else prod.shop_id
                rec = {
                    "product_id": prod.id,
                    "product_name": prod.name,
                    "variant_info": item_variant_map.get(prod.id),
                    "unit_price": unit_price,
                    "quantity": qty,
                    "line_total": line_total,
                    "shop_id": shop_id,
                }
                line_records.append(rec)
                if shop_id:
                    shop_items_map.setdefault(shop_id, []).append(rec)

            # Atomic stock deduction
            for rec in line_records:
                res = session.execute(
                    update(Inventory)
                    .where(
                        Inventory.city_id == city.id,
                        Inventory.product_id == rec["product_id"],
                        Inventory.stock_quantity >= rec["quantity"],
                    )
                    .values(stock_quantity=Inventory.stock_quantity - rec["quantity"])
                )
                if res.rowcount != 1:
                    raise OrderProcessingError(f"Concurrent stock conflict for '{rec['product_name']}'.")

            subtotal_val, shipping_val, total_val = calculate_totals(subtotal)
            clean_email = req.customer_email.strip().lower()

            # Find or link customer
            customer = session.execute(select(Customer).where(Customer.email == clean_email)).scalar_one_or_none()

            order = Order(
                order_number=generate_order_number(),
                idempotency_key=req.idempotency_key,
                customer_id=customer.id if customer else None,
                city_id=city.id,
                customer_name=req.customer_name,
                customer_email=clean_email,
                customer_phone=req.customer_phone,
                shipping_address=req.shipping_address,
                pincode=req.pincode,
                subtotal=subtotal_val,
                shipping_fee=shipping_val,
                total=total_val,
                status="CONFIRMED",
            )
            session.add(order)
            session.flush()

            # Create shop-specific suborders
            suborder_map: dict[int, SubOrder] = {}
            for idx, (s_id, s_items) in enumerate(shop_items_map.items(), start=1):
                s_subtotal = sum(i["line_total"] for i in s_items)
                suborder = SubOrder(
                    parent_order_id=order.id,
                    shop_id=s_id,
                    suborder_number=f"{order.order_number}-S{idx}",
                    subtotal=s_subtotal,
                    status="CONFIRMED",
                )
                session.add(suborder)
                session.flush()
                suborder_map[s_id] = suborder

            # Create order items linked to suborders
            for rec in line_records:
                suborder = suborder_map.get(rec["shop_id"])
                session.add(
                    OrderItem(
                        order_id=order.id,
                        suborder_id=suborder.id if suborder else None,
                        product_id=rec["product_id"],
                        shop_id=rec["shop_id"],
                        product_name=rec["product_name"],
                        variant_info=rec["variant_info"],
                        unit_price=rec["unit_price"],
                        quantity=rec["quantity"],
                        line_total=rec["line_total"],
                    )
                )

            # Write event to Transactional Outbox
            event_id = f"evt-{uuid.uuid4().hex}"
            payload = {
                "event_id": event_id,
                "event_type": "order.created",
                "order_id": order.id,
                "order_number": order.order_number,
                "city_code": city.code,
                "customer_email": order.customer_email,
                "total": str(order.total),
                "suborders": [
                    {
                        "suborder_id": sub.id,
                        "suborder_number": sub.suborder_number,
                        "shop_id": sub.shop_id,
                        "subtotal": str(sub.subtotal),
                    }
                    for sub in suborder_map.values()
                ],
            }
            session.add(
                OutboxEvent(
                    event_id=event_id,
                    aggregate_type="Order",
                    aggregate_id=str(order.id),
                    event_type="order.created",
                    payload=json.dumps(payload),
                    status="PENDING",
                )
            )
            session.flush()
            return _build_order_dto(session, order)
    except OrderProcessingError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error during order placement")
        raise OrderProcessingError("Unable to complete your order right now. Please try again.") from exc


def update_suborder_status(suborder_id: int, new_status: str, shop_id: Optional[int] = None) -> bool:
    """Seller operation: update status of a shop's suborder and emit outbox event."""
    with get_db_session() as session:
        suborder = session.execute(select(SubOrder).where(SubOrder.id == suborder_id)).scalar_one_or_none()
        if not suborder:
            return False
        if shop_id is not None and suborder.shop_id != shop_id:
            raise PermissionError("Access denied: You can only update suborders belonging to your own shop.")

        suborder.status = new_status
        session.flush()

        event_id = f"evt-{uuid.uuid4().hex}"
        payload = {
            "event_id": event_id,
            "event_type": "order.status_updated",
            "suborder_id": suborder.id,
            "suborder_number": suborder.suborder_number,
            "parent_order_id": suborder.parent_order_id,
            "shop_id": suborder.shop_id,
            "status": new_status,
        }
        session.add(
            OutboxEvent(
                event_id=event_id,
                aggregate_type="SubOrder",
                aggregate_id=str(suborder.id),
                event_type="order.status_updated",
                payload=json.dumps(payload),
                status="PENDING",
            )
        )
        session.flush()
        return True


def get_orders_for_customer(email: str) -> List[OrderConfirmationDTO]:
    """Retrieve all orders placed by the given customer email."""
    with get_db_session() as session:
        orders = session.execute(
            select(Order).where(Order.customer_email == email.strip().lower()).order_by(desc(Order.created_at))
        ).scalars().all()
        return [_build_order_dto(session, o) for o in orders]


def get_suborders_for_shop(shop_id: int) -> List[SubOrderDTO]:
    """Retrieve all incoming suborders for a seller shop."""
    with get_db_session() as session:
        suborders = session.execute(
            select(SubOrder, Shop)
            .join(Shop, Shop.id == SubOrder.shop_id)
            .where(SubOrder.shop_id == shop_id)
            .order_by(desc(SubOrder.created_at))
        ).all()

        results = []
        for sub, shop in suborders:
            items = session.execute(
                select(OrderItem).where(OrderItem.suborder_id == sub.id)
            ).scalars().all()
            item_dtos = [
                OrderItemDTO(
                    product_id=i.product_id,
                    product_name=i.product_name,
                    variant_info=i.variant_info,
                    unit_price=Decimal(i.unit_price),
                    quantity=i.quantity,
                    line_total=Decimal(i.line_total),
                    shop_id=shop.id,
                    shop_name=shop.shop_name,
                )
                for i in items
            ]
            results.append(
                SubOrderDTO(
                    id=sub.id,
                    suborder_number=sub.suborder_number,
                    shop_id=shop.id,
                    shop_name=shop.shop_name,
                    shop_code=shop.shop_code,
                    subtotal=Decimal(sub.subtotal),
                    status=sub.status,
                    created_at=sub.created_at,
                    items=item_dtos,
                )
            )
        return results


def get_order_by_id(
    order_id: int, user_email: Optional[str] = None, is_admin: bool = False
) -> Optional[OrderConfirmationDTO]:
    """Retrieve order by ID, enforcing user ownership unless admin."""
    with get_db_session() as session:
        order = session.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
        if not order:
            return None
        if not is_admin and user_email and order.customer_email.lower() != user_email.strip().lower():
            raise PermissionError("Access denied: You do not have permission to view this order.")
        return _build_order_dto(session, order)


def get_operations_metrics() -> dict:
    with get_db_session() as session:
        total_products = session.execute(select(func.count(Product.id))).scalar() or 0
        total_shops = session.execute(select(func.count(Shop.id))).scalar() or 0
        total_customers = session.execute(select(func.count(Customer.id))).scalar() or 0
        total_orders = session.execute(select(func.count(Order.id))).scalar() or 0
        total_revenue = session.execute(select(func.coalesce(func.sum(Order.total), 0))).scalar() or Decimal("0.00")
        total_inventory = session.execute(select(func.coalesce(func.sum(Inventory.stock_quantity), 0))).scalar() or 0
        pending_outbox = (
            session.execute(select(func.count(OutboxEvent.id)).where(OutboxEvent.status == "PENDING")).scalar() or 0
        )

        city_rows = session.execute(
            select(City.name, City.state, City.code, func.coalesce(func.sum(Inventory.stock_quantity), 0))
            .outerjoin(Inventory, Inventory.city_id == City.id)
            .group_by(City.id, City.name, City.state, City.code)
            .order_by(City.id)
        ).all()

        low_stock_rows = session.execute(
            select(Product.sku, Product.name, City.name, Inventory.stock_quantity)
            .join(Inventory, Inventory.product_id == Product.id)
            .join(City, City.id == Inventory.city_id)
            .where(Inventory.stock_quantity <= settings.LOW_STOCK_THRESHOLD)
            .order_by(Inventory.stock_quantity.asc(), Product.name.asc())
        ).all()

        recent_orders_rows = session.execute(
            select(Order, City.name).join(City, City.id == Order.city_id).order_by(desc(Order.created_at)).limit(10)
        ).all()

        outbox_rows = session.execute(select(OutboxEvent).order_by(desc(OutboxEvent.created_at)).limit(10)).scalars().all()

        return {
            "total_products": int(total_products),
            "total_shops": int(total_shops),
            "total_customers": int(total_customers),
            "total_orders": int(total_orders),
            "total_revenue": Decimal(total_revenue),
            "total_inventory": int(total_inventory),
            "pending_outbox": int(pending_outbox),
            "city_inventory": [{"City": f"{r[0]}, {r[1]}", "Code": r[2], "Available Units": int(r[3])} for r in city_rows],
            "low_stock": [{"SKU": r[0], "Product": r[1], "City": r[2], "Stock Left": int(r[3])} for r in low_stock_rows],
            "recent_orders": [
                {
                    "Order #": o.order_number,
                    "Customer": o.customer_name,
                    "City": cname,
                    "Total (₹)": float(o.total),
                    "Status": o.status,
                    "Placed At": o.created_at.strftime("%Y-%m-%d %H:%M UTC"),
                }
                for o, cname in recent_orders_rows
            ],
            "outbox_events": [
                {
                    "Event ID": e.event_id,
                    "Type": e.event_type,
                    "Aggregate": f"{e.aggregate_type}#{e.aggregate_id}",
                    "Status": e.status,
                    "Created": e.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for e in outbox_rows
            ],
        }
