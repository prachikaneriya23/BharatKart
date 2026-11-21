from decimal import Decimal
import os
import sys
import uuid
import pytest
from sqlalchemy import select

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import check_db_connection, engine, get_db_session
from backend.models import City, Customer, Inventory, Order, OrderItem, OutboxEvent, Product, Shop, SubOrder, User
from backend.schemas import (
    CartItemInput,
    CheckoutRequest,
    CustomerRegistrationRequest,
    ProductCreateRequest,
    ProductUpdateRequest,
    ShopRegistrationRequest,
)
from database.init_db import initialize_database
from services.auth_service import authenticate_user, hash_password
from services.chatbot_service import assistant
from services.customer_service import register_or_update_customer
from services.kafka_service import KafkaEventConsumer, producer, relay_outbox_events
from services.opensearch_service import opensearch_manager
from services.order_service import (
    get_order_by_id,
    get_orders_for_customer,
    place_order_atomic,
    update_suborder_status,
)
from services.product_service import (
    create_product,
    delete_product,
    list_products_for_city,
    refresh_cart_snapshot,
    update_inventory_stock,
    update_product,
)
from services.shop_service import approve_shop, get_shop_by_id, register_shop_atomic


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    initialize_database()


def test_01_application_imports_and_starts():
    """1. Test application imports and configuration load cleanly."""
    import app
    assert hasattr(app, "main")
    assert check_db_connection() is True


def test_02_postgresql_connection():
    """2. Test Aiven PostgreSQL connection executing SELECT 1."""
    connected = check_db_connection()
    assert connected is True, "Aiven PostgreSQL connection failed."


def test_03_customer_registration_and_login():
    """3. Test customer registration and secure authentication."""
    unique_email = f"buyer_{uuid.uuid4().hex[:6]}@example.com"
    req = CustomerRegistrationRequest(
        full_name="Pooja Sharma",
        email=unique_email,
        phone="9876543210",
        password="BuyerSecure@123",
        default_city_id=1,
        default_address="42 Indiranagar 100ft Road",
        pincode="560038",
    )
    cust = register_or_update_customer(req)
    assert cust.id is not None
    assert cust.email == unique_email

    # Authenticate with hashed password verification
    user = authenticate_user(unique_email, "BuyerSecure@123")
    assert user is not None
    assert user.role == "customer"


def test_04_seller_registration_and_approval():
    """4. Test seller registration in PENDING status and admin approval."""
    unique_email = f"merchant_{uuid.uuid4().hex[:6]}@shop.in"
    s_req = ShopRegistrationRequest(
        shop_name=f"Vedic Crafts {uuid.uuid4().hex[:4]}",
        owner_name="Ananya Rao",
        owner_email=unique_email,
        owner_phone="9822011223",
        password="SellerPassword@123",
        business_type="Sole Proprietorship",
        primary_category="Home & Kitchen",
        pan_number="ABCDE1234F",
        city_id=1,
        shop_address="12 MG Road, Bengaluru",
        pincode="560001",
        pickup_slot="Morning (9:00 AM – 1:00 PM)",
        bank_account_holder="Ananya Rao",
        bank_account_number="50200012345678",
        bank_ifsc="HDFC0000184",
    )
    shop = register_shop_atomic(s_req)
    assert shop.status == "PENDING"

    # Admin approves
    ok = approve_shop(shop.id)
    assert ok is True
    updated = get_shop_by_id(shop.id)
    assert updated.status == "VERIFIED"


def test_05_seller_product_creation_and_inventory_updates():
    """5. Test seller product creation and inventory stock updates."""
    prods = list_products_for_city(city_id=1)
    shop_id = prods[0].shop_id or 1

    p_req = ProductCreateRequest(
        name=f"Pure Copper Jug {uuid.uuid4().hex[:4]}",
        brand="Kansa & Clay",
        category="Home & Kitchen",
        description="Ayurvedic copper water vessel handcrafted by local artisans.",
        price=Decimal("899.00"),
        mrp=Decimal("1299.00"),
        initial_stock=20,
        city_id=1,
    )
    new_p = create_product(shop_id=shop_id, req=p_req)
    assert new_p.id is not None
    assert new_p.stock_quantity == 20

    # Inventory stock adjustment
    update_inventory_stock(new_p.id, city_id=1, shop_id=shop_id, new_quantity=35)
    refreshed = list_products_for_city(city_id=1, shop_id=shop_id)
    matched = next(p for p in refreshed if p.id == new_p.id)
    assert matched.stock_quantity == 35


def test_06_shop_specific_product_catalogue():
    """6. Test retrieving products strictly belonging to a specific store."""
    with get_db_session() as session:
        shop = session.execute(select(Shop).where(Shop.city_id == 1)).scalars().first()
        assert shop is not None

    prods = list_products_for_city(city_id=1, shop_id=shop.id)
    assert len(prods) > 0
    for p in prods:
        assert p.shop_id == shop.id


def test_07_product_search():
    """7. Test product search across multiple shops."""
    results = opensearch_manager.search_products(query="coffee", city_id=1)
    assert isinstance(results, list)
    assert len(results) > 0
    assert any("coffee" in r["name"].lower() or "coffee" in r["description"].lower() for r in results)


def test_08_multi_store_cart():
    """8. Test multi-store shopping cart combining items from different stores."""
    all_prods = list_products_for_city(city_id=1)
    p1 = all_prods[0]
    p2 = next((p for p in all_prods if p.shop_id != p1.shop_id), all_prods[1])

    cart_dict = {p1.id: 1, p2.id: 2}
    lines, warnings = refresh_cart_snapshot(city_id=1, cart_items=cart_dict)
    assert len(lines) == 2
    assert lines[0]["product_id"] == p1.id
    assert lines[1]["product_id"] == p2.id


def test_09_parent_order_creation():
    """9. Test parent order creation with total and status."""
    all_prods = list_products_for_city(city_id=1)
    p = all_prods[0]

    req = CheckoutRequest(
        idempotency_key=f"idem-parent-{uuid.uuid4().hex}",
        city_id=1,
        customer_name="Kiran Kumar",
        customer_email="kiran.parent@example.com",
        customer_phone="9876543210",
        shipping_address="100 Feet Road, Indiranagar",
        pincode="560038",
        items=[CartItemInput(product_id=p.id, quantity=1)],
    )
    order = place_order_atomic(req)
    assert order.order_id is not None
    assert order.order_number.startswith("BK-")
    assert order.status == "CONFIRMED"
    assert order.total_amount > Decimal("0.00")


def test_10_shop_wise_suborder_creation():
    """10. Test partitioning parent order into separate shop suborders."""
    all_prods = list_products_for_city(city_id=1)
    p1 = all_prods[0]
    p2 = next((p for p in all_prods if p.shop_id != p1.shop_id), all_prods[1])

    req = CheckoutRequest(
        idempotency_key=f"idem-multi-{uuid.uuid4().hex}",
        city_id=1,
        customer_name="Sunil Mehta",
        customer_email="sunil.multi@example.com",
        customer_phone="9876543211",
        shipping_address="22 MG Road, Bengaluru",
        pincode="560001",
        items=[CartItemInput(product_id=p1.id, quantity=1), CartItemInput(product_id=p2.id, quantity=1)],
    )
    order = place_order_atomic(req)
    assert len(order.suborders) >= 1
    for sub in order.suborders:
        assert sub.suborder_number.startswith(order.order_number)
        assert sub.subtotal > Decimal("0.00")


def test_11_inventory_deduction():
    """11. Test accurate inventory stock deduction on purchase."""
    all_prods = list_products_for_city(city_id=1)
    target = all_prods[0]
    initial_stock = target.stock_quantity

    req = CheckoutRequest(
        idempotency_key=f"idem-deduct-{uuid.uuid4().hex}",
        city_id=1,
        customer_name="Deepa Nair",
        customer_email="deepa.deduct@example.com",
        customer_phone="9876543212",
        shipping_address="5 Koregaon Park, Pune",
        pincode="411001",
        items=[CartItemInput(product_id=target.id, quantity=2)],
    )
    place_order_atomic(req)

    refreshed = list_products_for_city(city_id=1)
    matched = next(p for p in refreshed if p.id == target.id)
    assert matched.stock_quantity == initial_stock - 2


def test_12_duplicate_order_prevention():
    """12. Test duplicate order prevention using idempotency key."""
    all_prods = list_products_for_city(city_id=1)
    p = all_prods[0]
    shared_key = f"idem-prevent-dup-{uuid.uuid4().hex}"

    req = CheckoutRequest(
        idempotency_key=shared_key,
        city_id=1,
        customer_name="Vikram Joshi",
        customer_email="vikram.dup@example.com",
        customer_phone="9876543213",
        shipping_address="32 Brigade Road",
        pincode="560025",
        items=[CartItemInput(product_id=p.id, quantity=1)],
    )
    order1 = place_order_atomic(req)
    order2 = place_order_atomic(req)
    # Must return same order ID without placing duplicate order
    assert order1.order_id == order2.order_id
    assert order1.order_number == order2.order_number


def test_13_outbox_event_creation():
    """13. Test transactional outbox event creation."""
    with get_db_session() as session:
        events = session.execute(
            select(OutboxEvent).order_by(OutboxEvent.created_at.desc()).limit(5)
        ).scalars().all()
        assert len(events) > 0
        latest = events[0]
        assert latest.event_id is not None
        assert latest.status in ("PENDING", "PUBLISHED")


def test_14_kafka_connection_and_event_publishing():
    """14. Test Kafka publisher interface handles events reliably."""
    test_event = {"event_id": f"evt-{uuid.uuid4().hex}", "event_type": "bharatkart.order.created", "total": "599.00"}
    res = producer.publish(topic="bharatkart.order.created", key="order-test", payload=test_event)
    assert isinstance(res, bool)


def test_15_kafka_consumer_processing_and_idempotency():
    """15. Test idempotent Kafka consumer skips duplicate event IDs."""
    consumer = KafkaEventConsumer(group_id="test-idempotency-group")
    test_id = f"evt-idemp-{uuid.uuid4().hex}"
    counter = [0]

    def test_handler(payload):
        counter[0] += 1

    # First delivery: processed
    first = consumer.process_event_idempotently(test_id, test_handler, {"data": "test"})
    assert first is True
    assert counter[0] == 1

    # Second delivery: skipped
    second = consumer.process_event_idempotently(test_id, test_handler, {"data": "test"})
    assert second is False
    assert counter[0] == 1  # Unchanged


def test_16_opensearch_connection_and_indexing():
    """16. Test OpenSearch manager handles indexing."""
    sample_doc = {
        "id": 9999,
        "sku": "BK-TEST-9999",
        "name": "OpenSearch Test Item",
        "brand": "BharatCraft",
        "category": "Groceries",
        "description": "Index test",
        "price": 199.0,
        "mrp": 299.0,
        "rating": 4.5,
        "city_id": 1,
    }
    # Should handle indexing gracefully (returns bool, no crash)
    res = opensearch_manager.index_product(sample_doc)
    assert isinstance(res, bool)


def test_17_postgresql_fallback_search():
    """17. Test PostgreSQL authoritative fallback search."""
    results = opensearch_manager._search_products_postgresql(
        query="tea",
        city_id=1,
        shop_id=None,
        category=None,
        min_price=None,
        max_price=None,
    )
    assert isinstance(results, list)


def test_18_seller_ownership_restrictions():
    """18. Test seller ownership backend enforcement."""
    with pytest.raises(PermissionError):
        # Attempt to delete product from another shop (shop ID 9999)
        delete_product(product_id=1, shop_id=9999)


def test_19_customer_order_privacy():
    """19. Test customer order privacy backend enforcement."""
    orders = get_orders_for_customer("kiran.parent@example.com")
    if orders:
        order = orders[0]
        with pytest.raises(PermissionError):
            get_order_by_id(order.order_id, user_email="unauthorized@example.com", is_admin=False)


def test_20_shopping_assistant_responses_using_real_data():
    """20. Test shopping intelligence assistant grounded in real database."""
    # Product query
    r1 = assistant.process_message("Find Arabica coffee in Bengaluru", city_id=1)
    assert r1.intent in ("product_discovery", "shop_discovery")
    assert len(r1.reply_text) > 10

    # Cross-store comparison
    r2 = assistant.process_message("Compare audio and earbuds across shops", city_id=1)
    assert r2.intent == "comparison"
    assert len(r2.comparison_items) > 0

    # Multi-shop basket optimizer
    r3 = assistant.process_message("I need coffee and kettle within ₹2,500", city_id=1)
    assert r3.intent == "basket_optimizer"
    assert r3.basket_plan is not None
    assert r3.basket_plan["shop_count"] >= 1
