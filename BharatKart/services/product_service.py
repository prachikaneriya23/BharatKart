from decimal import Decimal
import json
import logging
from typing import List, Optional
import uuid
from sqlalchemy import asc, desc, func, or_, select
import streamlit as st
from backend.database import get_db_session
from backend.models import City, Inventory, OutboxEvent, Product, ProductVariant, Shop
from backend.schemas import (
    CityDTO,
    ProductCardDTO,
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductVariantDTO,
)
from utils.helpers import get_product_photo_url

logger = logging.getLogger(__name__)


def _to_product_dto(
    product: Product,
    inv: Inventory,
    city: City,
    shop: Optional[Shop] = None,
    variants: Optional[List[ProductVariant]] = None,
) -> ProductCardDTO:
    discount = 0
    if product.mrp and product.mrp > 0 and product.mrp > product.price:
        discount = int(round(((product.mrp - product.price) / product.mrp) * 100))

    img = product.image_url or ""
    if (
        not img.startswith("https://")
        or "photo-1544787219-7f47ccb76574" in img
        or "photo-1514432324607-a09d9b4aefdd" in img
        or ("photo-1523275335684-37898b6baf30" in img and product.category != "Electronics")
    ):
        img = get_product_photo_url(product.sku, category=product.category, name=product.name)

    variant_dtos = [
        ProductVariantDTO(
            id=v.id,
            variant_name=v.variant_name,
            variant_value=v.variant_value,
            price_adjustment=Decimal(v.price_adjustment),
            sku_modifier=v.sku_modifier,
            stock_quantity=v.stock_quantity,
        )
        for v in (variants or [])
    ]

    return ProductCardDTO(
        id=product.id,
        sku=product.sku,
        name=product.name,
        brand=product.brand,
        category=product.category,
        description=product.description,
        image_url=img,
        price=Decimal(product.price),
        mrp=Decimal(product.mrp),
        discount_percent=discount,
        rating=Decimal(product.rating),
        is_featured=product.is_featured,
        city_id=city.id,
        city_name=f"{city.name}, {city.state}",
        stock_quantity=inv.stock_quantity if inv else 0,
        shop_id=shop.id if shop else (product.shop_id or None),
        shop_name=shop.shop_name if shop else None,
        shop_code=shop.shop_code if shop else None,
        variants=variant_dtos,
    )


@st.cache_data(ttl=60, show_spinner=False)
def get_active_cities() -> List[CityDTO]:
    with get_db_session() as session:
        rows = session.execute(select(City).where(City.is_active.is_(True)).order_by(City.id)).scalars().all()
        return [CityDTO(id=c.id, name=c.name, state=c.state, code=c.code) for c in rows]


@st.cache_data(ttl=60, show_spinner=False)
def get_categories() -> List[str]:
    with get_db_session() as session:
        rows = session.execute(select(Product.category).distinct().order_by(Product.category)).scalars().all()
        return list(rows)


def _seed_products_for_shop(session, shop_id: int) -> None:
    shop = session.execute(select(Shop).where(Shop.id == shop_id)).scalar_one_or_none()
    if not shop:
        return

    cities = session.execute(select(City)).scalars().all()
    starter_items = [
        {
            "sku_suffix": "001",
            "name": "Pure Brass Peacock Diya Lamp",
            "category": "Home & Kitchen",
            "description": f"Hand-cast traditional pure brass peacock oil lamp offered by {shop.shop_name}.",
            "price": Decimal("849.00"),
            "mrp": Decimal("1299.00"),
            "rating": Decimal("4.85"),
            "is_featured": True,
            "image_url": "https://images.unsplash.com/photo-1577083753695-e010191bacb5?auto=format&fit=crop&w=800&q=85",
            "stock": 25,
            "variants": [
                {"variant_name": "Finish", "variant_value": "Antique Gold", "price_adjustment": Decimal("0.00"), "stock_quantity": 15},
                {"variant_name": "Finish", "variant_value": "Polished Brass", "price_adjustment": Decimal("100.00"), "stock_quantity": 10},
            ],
        },
        {
            "sku_suffix": "002",
            "name": "Handcrafted Rosewood Elephant Sculpture",
            "category": "Home & Kitchen",
            "description": f"Intricately hand-carved Mysore rosewood elephant sculpture from {shop.shop_name}.",
            "price": Decimal("1199.00"),
            "mrp": Decimal("1799.00"),
            "rating": Decimal("4.90"),
            "is_featured": True,
            "image_url": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=800&q=85",
            "stock": 20,
            "variants": [
                {"variant_name": "Size", "variant_value": "6-Inch Miniature", "price_adjustment": Decimal("0.00"), "stock_quantity": 12},
                {"variant_name": "Size", "variant_value": "9-Inch Grand", "price_adjustment": Decimal("450.00"), "stock_quantity": 8},
            ],
        },
        {
            "sku_suffix": "003",
            "name": "Hammered Pure Copper Water Dispenser (5L)",
            "category": "Home & Kitchen",
            "description": f"Ayurvedic 99.7% pure certified copper dispenser offered by {shop.shop_name}.",
            "price": Decimal("1899.00"),
            "mrp": Decimal("2599.00"),
            "rating": Decimal("4.88"),
            "is_featured": True,
            "image_url": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=800&q=85",
            "stock": 18,
            "variants": [
                {"variant_name": "Capacity", "variant_value": "5 Litre", "price_adjustment": Decimal("0.00"), "stock_quantity": 10},
                {"variant_name": "Capacity", "variant_value": "8 Litre Jumbo", "price_adjustment": Decimal("500.00"), "stock_quantity": 8},
            ],
        },
        {
            "sku_suffix": "004",
            "name": "Cast Iron Pre-Seasoned Dosa Tawa (10-Inch)",
            "category": "Home & Kitchen",
            "description": f"Heavy-gauge pure cast iron flat skillet pre-seasoned with cold-pressed oil from {shop.shop_name}.",
            "price": Decimal("999.00"),
            "mrp": Decimal("1499.00"),
            "rating": Decimal("4.79"),
            "is_featured": False,
            "image_url": "https://images.unsplash.com/photo-1585515320310-259814833e62?auto=format&fit=crop&w=800&q=85",
            "stock": 30,
            "variants": [
                {"variant_name": "Diameter", "variant_value": "10-Inch Standard", "price_adjustment": Decimal("0.00"), "stock_quantity": 18},
                {"variant_name": "Diameter", "variant_value": "12-Inch Family", "price_adjustment": Decimal("250.00"), "stock_quantity": 12},
            ],
        },
        {
            "sku_suffix": "005",
            "name": "Aromatherapy Solid Brass Dhuna / Dhoop Burner",
            "category": "Home & Kitchen",
            "description": f"Traditional hand-turned solid brass loban and sambrani dhoop burner from {shop.shop_name}.",
            "price": Decimal("649.00"),
            "mrp": Decimal("950.00"),
            "rating": Decimal("4.82"),
            "is_featured": False,
            "image_url": "https://images.unsplash.com/photo-1602928321679-560bb453f190?auto=format&fit=crop&w=800&q=85",
            "stock": 22,
            "variants": [
                {"variant_name": "Handle", "variant_value": "Natural Sheesham", "price_adjustment": Decimal("0.00"), "stock_quantity": 14},
                {"variant_name": "Handle", "variant_value": "Carved Rosewood", "price_adjustment": Decimal("120.00"), "stock_quantity": 8},
            ],
        },
    ]

    for item in starter_items:
        sku = f"BK-SHP{shop.id}-{item['sku_suffix']}"
        existing = session.execute(select(Product).where(Product.sku == sku)).scalar_one_or_none()
        if not existing:
            p = Product(
                sku=sku,
                name=item["name"],
                brand=shop.shop_name,
                category=item["category"],
                description=item["description"],
                price=item["price"],
                mrp=item["mrp"],
                rating=item["rating"],
                is_featured=item["is_featured"],
                image_url=item["image_url"],
                shop_id=shop.id,
            )
            session.add(p)
            session.flush()

            for v in item["variants"]:
                session.add(ProductVariant(product_id=p.id, **v))

            for c in cities:
                session.add(Inventory(product_id=p.id, city_id=c.id, shop_id=shop.id, stock_quantity=item["stock"]))

    session.flush()


def list_products_for_city(
    city_id: int,
    shop_id: Optional[int] = None,
    search_query: str = "",
    category: str = "All",
    sort_by: str = "Featured",
    only_featured: bool = False,
    in_stock_only: bool = False,
) -> List[ProductCardDTO]:
    with get_db_session() as session:
        if shop_id is not None:
            p_count = session.execute(select(func.count(Product.id)).where(Product.shop_id == shop_id)).scalar()
            if p_count == 0:
                _seed_products_for_shop(session, shop_id)

        stmt = (
            select(Product, Inventory, City, Shop)
            .join(Inventory, Inventory.product_id == Product.id)
            .join(City, City.id == Inventory.city_id)
            .outerjoin(Shop, Shop.id == Product.shop_id)
            .where(City.id == city_id)
        )

        if shop_id is not None:
            stmt = stmt.where(Product.shop_id == shop_id)
        if only_featured:
            stmt = stmt.where(Product.is_featured.is_(True))
        if category and category != "All":
            stmt = stmt.where(Product.category == category)
        if in_stock_only:
            stmt = stmt.where(Inventory.stock_quantity > 0)
        if search_query and search_query.strip():
            term = f"%{search_query.strip()}%"
            stmt = stmt.where(
                or_(
                    Product.name.ilike(term),
                    Product.brand.ilike(term),
                    Product.category.ilike(term),
                    Product.description.ilike(term),
                    Shop.shop_name.ilike(term),
                )
            )

        if sort_by == "Price: Low to High":
            stmt = stmt.order_by(asc(Product.price))
        elif sort_by == "Price: High to Low":
            stmt = stmt.order_by(desc(Product.price))
        elif sort_by == "Top Rated":
            stmt = stmt.order_by(desc(Product.rating))
        elif sort_by == "Availability":
            stmt = stmt.order_by(desc(Inventory.stock_quantity), desc(Product.is_featured))
        else:
            stmt = stmt.order_by(desc(Product.is_featured), asc(Product.id))

        results = session.execute(stmt).all()
        dtos = []
        for prod, inv, city, shop in results:
            variants = session.execute(
                select(ProductVariant).where(ProductVariant.product_id == prod.id)
            ).scalars().all()
            dtos.append(_to_product_dto(prod, inv, city, shop, variants))
        return dtos


def get_product_detail(product_id: int, city_id: int) -> Optional[ProductCardDTO]:
    with get_db_session() as session:
        row = session.execute(
            select(Product, Inventory, City, Shop)
            .join(Inventory, Inventory.product_id == Product.id)
            .join(City, City.id == Inventory.city_id)
            .outerjoin(Shop, Shop.id == Product.shop_id)
            .where(Product.id == product_id, City.id == city_id)
        ).first()
        if not row:
            return None
        prod, inv, city, shop = row
        variants = session.execute(
            select(ProductVariant).where(ProductVariant.product_id == prod.id)
        ).scalars().all()
        return _to_product_dto(prod, inv, city, shop, variants)


def create_product(shop_id: int, req: ProductCreateRequest) -> ProductCardDTO:
    """Seller operation: add new product belonging to seller shop, emit product.created outbox event."""
    with get_db_session() as session:
        shop = session.execute(select(Shop).where(Shop.id == shop_id)).scalar_one_or_none()
        if not shop:
            raise ValueError(f"Shop with ID {shop_id} not found.")

        city = session.execute(select(City).where(City.id == req.city_id)).scalar_one_or_none()
        if not city:
            raise ValueError(f"City with ID {req.city_id} not found.")

        sku = f"BK-{shop.shop_code[-3:]}-{uuid.uuid4().hex[:6].upper()}"
        img_url = req.image_url.strip() if req.image_url else get_product_photo_url(sku)

        product = Product(
            shop_id=shop.id,
            sku=sku,
            name=req.name.strip(),
            brand=req.brand.strip(),
            category=req.category.strip(),
            description=req.description.strip(),
            image_url=img_url,
            price=Decimal(req.price),
            mrp=Decimal(req.mrp),
            rating=Decimal("4.50"),
            is_featured=req.is_featured,
        )
        session.add(product)
        session.flush()

        inv = Inventory(
            city_id=city.id,
            product_id=product.id,
            shop_id=shop.id,
            stock_quantity=req.initial_stock,
        )
        session.add(inv)
        session.flush()

        event_id = f"evt-{uuid.uuid4().hex}"
        payload = {
            "event_id": event_id,
            "event_type": "product.created",
            "product_id": product.id,
            "sku": product.sku,
            "name": product.name,
            "shop_id": shop.id,
            "shop_name": shop.shop_name,
            "city_id": city.id,
            "price": str(product.price),
            "stock": inv.stock_quantity,
        }
        session.add(
            OutboxEvent(
                event_id=event_id,
                aggregate_type="Product",
                aggregate_id=str(product.id),
                event_type="product.created",
                payload=json.dumps(payload),
                status="PENDING",
            )
        )
        session.flush()
        return _to_product_dto(product, inv, city, shop, [])


def update_product(product_id: int, shop_id: int, req: ProductUpdateRequest) -> ProductCardDTO:
    """Seller operation: update product with ownership verification and outbox event."""
    with get_db_session() as session:
        product = session.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
        if not product:
            raise ValueError("Product not found.")
        if product.shop_id != shop_id:
            raise PermissionError("Access denied: You can only edit products belonging to your shop.")

        if req.name is not None:
            product.name = req.name.strip()
        if req.brand is not None:
            product.brand = req.brand.strip()
        if req.category is not None:
            product.category = req.category.strip()
        if req.description is not None:
            product.description = req.description.strip()
        if req.price is not None:
            product.price = Decimal(req.price)
        if req.mrp is not None:
            product.mrp = Decimal(req.mrp)
        if req.image_url is not None:
            product.image_url = req.image_url.strip()
        if req.is_featured is not None:
            product.is_featured = req.is_featured

        session.flush()

        event_id = f"evt-{uuid.uuid4().hex}"
        payload = {
            "event_id": event_id,
            "event_type": "product.updated",
            "product_id": product.id,
            "sku": product.sku,
            "name": product.name,
            "shop_id": product.shop_id,
            "price": str(product.price),
        }
        session.add(
            OutboxEvent(
                event_id=event_id,
                aggregate_type="Product",
                aggregate_id=str(product.id),
                event_type="product.updated",
                payload=json.dumps(payload),
                status="PENDING",
            )
        )
        session.flush()

        inv = session.execute(select(Inventory).where(Inventory.product_id == product.id)).scalar_one_or_none()
        city = session.execute(select(City).where(City.id == (inv.city_id if inv else 1))).scalar_one()
        shop = session.execute(select(Shop).where(Shop.id == product.shop_id)).scalar_one_or_none()
        return _to_product_dto(product, inv, city, shop, [])


def delete_product(product_id: int, shop_id: int) -> bool:
    """Seller operation: delete product with ownership enforcement."""
    with get_db_session() as session:
        product = session.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
        if not product:
            return False
        if product.shop_id != shop_id:
            raise PermissionError("Access denied: You can only delete products belonging to your shop.")
        session.delete(product)
        session.flush()
        return True


def update_inventory_stock(product_id: int, city_id: int, shop_id: int, new_quantity: int) -> bool:
    """Update stock quantity and emit inventory.updated outbox event."""
    with get_db_session() as session:
        product = session.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
        if not product or product.shop_id != shop_id:
            raise PermissionError("Access denied: You can only update inventory for your shop's products.")

        inv = session.execute(
            select(Inventory).where(Inventory.product_id == product_id, Inventory.city_id == city_id)
        ).scalar_one_or_none()
        if not inv:
            inv = Inventory(product_id=product_id, city_id=city_id, shop_id=shop_id, stock_quantity=new_quantity)
            session.add(inv)
        else:
            inv.stock_quantity = new_quantity
        session.flush()

        event_id = f"evt-{uuid.uuid4().hex}"
        payload = {
            "event_id": event_id,
            "event_type": "inventory.updated",
            "product_id": product_id,
            "city_id": city_id,
            "shop_id": shop_id,
            "stock_quantity": new_quantity,
        }
        session.add(
            OutboxEvent(
                event_id=event_id,
                aggregate_type="Inventory",
                aggregate_id=f"{product_id}-{city_id}",
                event_type="inventory.updated",
                payload=json.dumps(payload),
                status="PENDING",
            )
        )
        session.flush()
        return True


def refresh_cart_snapshot(city_id: int, cart_items: dict[int, int]) -> tuple[list[dict], list[str]]:
    if not cart_items:
        return [], []
    warnings: list[str] = []
    lines: list[dict] = []
    with get_db_session() as session:
        product_ids = [int(pid) for pid in cart_items.keys()]
        rows = session.execute(
            select(Product, Inventory, Shop)
            .join(Inventory, Inventory.product_id == Product.id)
            .outerjoin(Shop, Shop.id == Product.shop_id)
            .where(Inventory.city_id == city_id, Product.id.in_(product_ids))
        ).all()
        lookup = {prod.id: (prod, inv, shop) for prod, inv, shop in rows}

        for pid_raw, requested_qty in list(cart_items.items()):
            pid = int(pid_raw)
            if pid not in lookup:
                warnings.append(f"Removed unavailable product ID {pid} from cart.")
                continue
            prod, inv, shop = lookup[pid]
            if inv.stock_quantity <= 0:
                warnings.append(f"'{prod.name}' is now out of stock in your selected city.")
                continue
            final_qty = min(int(requested_qty), inv.stock_quantity)
            if final_qty < int(requested_qty):
                warnings.append(
                    f"Adjusted '{prod.name}' quantity from {requested_qty} to {final_qty} due to live stock limits."
                )
            unit_price = Decimal(prod.price)
            img = prod.image_url if (prod.image_url and prod.image_url.startswith("https://")) else get_product_photo_url(prod.sku)
            lines.append(
                {
                    "product_id": prod.id,
                    "sku": prod.sku,
                    "name": prod.name,
                    "brand": prod.brand,
                    "category": prod.category,
                    "image_url": img,
                    "unit_price": unit_price,
                    "mrp": Decimal(prod.mrp),
                    "quantity": final_qty,
                    "stock_quantity": inv.stock_quantity,
                    "line_total": unit_price * final_qty,
                    "shop_id": shop.id if shop else prod.shop_id,
                    "shop_name": shop.shop_name if shop else "Independent Store",
                    "shop_code": shop.shop_code if shop else "SHP-LOCAL",
                }
            )
    return lines, warnings
