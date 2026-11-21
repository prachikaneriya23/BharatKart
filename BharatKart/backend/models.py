from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from backend.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    code = Column(String(10), nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    inventories = relationship("Inventory", back_populates="city", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="city")
    shops = relationship("Shop", back_populates="city")

    __table_args__ = (UniqueConstraint("name", "state", name="uq_city_name_state"),)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(150), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="customer")  # customer, seller, admin
    full_name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    customer_profile = relationship("Customer", back_populates="user", uselist=False)
    shops = relationship("Shop", back_populates="user")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=False)
    default_city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    default_address = Column(Text, nullable=False)
    pincode = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="customer_profile")
    city = relationship("City")
    orders = relationship("Order", back_populates="customer")


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    shop_code = Column(String(24), nullable=False, unique=True, index=True)
    shop_name = Column(String(180), nullable=False)
    owner_name = Column(String(150), nullable=False)
    owner_email = Column(String(150), nullable=False)
    owner_phone = Column(String(20), nullable=False)
    business_type = Column(String(80), nullable=False)
    primary_category = Column(String(80), nullable=False)
    gstin = Column(String(20), nullable=True)
    pan_number = Column(String(15), nullable=False)
    fssai_license = Column(String(30), nullable=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    shop_address = Column(Text, nullable=False)
    pincode = Column(String(10), nullable=False)
    pickup_slot = Column(String(80), nullable=False)
    bank_account_holder = Column(String(150), nullable=False)
    bank_account_number = Column(String(35), nullable=False)
    bank_ifsc = Column(String(20), nullable=False)
    upi_id = Column(String(100), nullable=True)
    shop_description = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="PENDING")  # PENDING, VERIFIED, REJECTED
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="shops")
    city = relationship("City", back_populates="shops")
    products = relationship("Product", back_populates="shop")
    suborders = relationship("SubOrder", back_populates="shop")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="SET NULL"), nullable=True, index=True)
    sku = Column(String(40), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    brand = Column(String(100), nullable=False, index=True)
    category = Column(String(80), nullable=False, index=True)
    description = Column(Text, nullable=False)
    image_url = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    mrp = Column(Numeric(10, 2), nullable=False)
    rating = Column(Numeric(3, 2), default=Decimal("4.50"), nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    shop = relationship("Shop", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    inventories = relationship("Inventory", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_product_price_nonneg"),
        CheckConstraint("mrp >= price", name="ck_product_mrp_gte_price"),
    )


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_name = Column(String(50), nullable=False)  # e.g. "Pack Size", "Color"
    variant_value = Column(String(80), nullable=False)  # e.g. "250g", "Olive Green"
    price_adjustment = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    sku_modifier = Column(String(30), nullable=True)
    stock_quantity = Column(Integer, default=10, nullable=False)

    product = relationship("Product", back_populates="variants")


class Inventory(Base):
    __tablename__ = "inventories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="SET NULL"), nullable=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    city = relationship("City", back_populates="inventories")
    product = relationship("Product", back_populates="inventories")

    __table_args__ = (
        UniqueConstraint("city_id", "product_id", name="uq_inventory_city_product"),
        CheckConstraint("stock_quantity >= 0", name="ck_inventory_stock_nonneg"),
        Index("ix_inventory_city_product", "city_id", "product_id"),
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(32), nullable=False, unique=True, index=True)
    idempotency_key = Column(String(64), nullable=False, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    customer_name = Column(String(150), nullable=False)
    customer_email = Column(String(150), nullable=False)
    customer_phone = Column(String(20), nullable=False)
    shipping_address = Column(Text, nullable=False)
    pincode = Column(String(10), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    shipping_fee = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    status = Column(String(30), nullable=False, default="CONFIRMED")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    city = relationship("City", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    suborders = relationship("SubOrder", back_populates="parent_order", cascade="all, delete-orphan")


class SubOrder(Base):
    """Shop-specific suborder partitioned from a parent order."""
    __tablename__ = "suborders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    suborder_number = Column(String(40), nullable=False, unique=True, index=True)
    subtotal = Column(Numeric(10, 2), nullable=False)
    status = Column(String(30), nullable=False, default="CONFIRMED")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    parent_order = relationship("Order", back_populates="suborders")
    shop = relationship("Shop", back_populates="suborders")
    items = relationship("OrderItem", back_populates="suborder")


# Alias so both spellings import correctly: `from backend.models import Suborder`
Suborder = SubOrder


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    suborder_id = Column(Integer, ForeignKey("suborders.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="SET NULL"), nullable=True, index=True)
    product_name = Column(String(200), nullable=False)
    variant_info = Column(String(100), nullable=True)
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    suborder = relationship("SubOrder", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    shop = relationship("Shop")


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), nullable=False, unique=True, index=True)
    aggregate_type = Column(String(50), nullable=False)
    aggregate_id = Column(String(64), nullable=False)
    event_type = Column(String(80), nullable=False)
    payload = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", index=True)  # PENDING, PUBLISHED, FAILED
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)


class ProcessedEvent(Base):
    """Idempotency record to prevent duplicate event consumption."""
    __tablename__ = "processed_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), nullable=False, unique=True, index=True)
    consumer_group = Column(String(64), nullable=False, default="default")
    processed_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)