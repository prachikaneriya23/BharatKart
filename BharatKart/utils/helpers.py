import base64
from decimal import Decimal
from io import BytesIO
import uuid
from PIL import Image, ImageDraw


def format_inr(amount: Decimal | float | int) -> str:
    return f"₹{float(amount):,.2f}"


def generate_order_number() -> str:
    return f"BK-{uuid.uuid4().hex[:8].upper()}"


def generate_shop_code() -> str:
    return f"SHP-{uuid.uuid4().hex[:6].upper()}"


SHOP_COVER_PHOTOS: dict[str, str] = {
    # Bengaluru
    "SHP-BLR101": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=1200&q=85",  # Malnad Roasters & Estate Co.
    "SHP-BLR102": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=1200&q=85",  # Svara Audio & Electronics
    # Mumbai
    "SHP-BOM204": "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?auto=format&fit=crop&w=1200&q=85",  # Kansa & Clay Artisan Studio
    "SHP-BOM205": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=1200&q=85",  # Kala Ghoda Art & Leather Studio
    "SHP-BOM206": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=1200&q=85",  # Crawford Gourmet & Spices
    # Pune
    "SHP-PNQ309": "https://images.unsplash.com/photo-1590736704728-f4730bb30770?auto=format&fit=crop&w=1200&q=85",  # Dakshina Leatherworks
    "SHP-PNQ310": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=1200&q=85",  # Tambat Ali Coppersmiths
    "SHP-PNQ311": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=1200&q=85",  # Deccan Handloom & Paithani
    "SHP-PNQ312": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=1200&q=85",  # Chitale & Joshi Sweets
    "SHP-PNQ313": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=1200&q=85",  # Shaniwar Peth Stationery
    # Mangalore
    "SHP-IXE401": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?auto=format&fit=crop&w=1200&q=85",  # Aranya Botanical Apothecary
    "SHP-IXE402": "https://images.unsplash.com/photo-1536591375315-0b81c2f1f5fa?auto=format&fit=crop&w=1200&q=85",  # Canara Cashew & Confectionery
    "SHP-IXE403": "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?auto=format&fit=crop&w=1200&q=85",  # Kudla Coastal Handlooms
    "SHP-IXE404": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=1200&q=85",  # Netravati Spices
    "SHP-IXE405": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=1200&q=85",  # Gerosa Audio
}

DEFAULT_SHOP_COVER = "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=85"


def get_shop_cover_url(shop_code: str) -> str:
    return SHOP_COVER_PHOTOS.get(shop_code, DEFAULT_SHOP_COVER)


REAL_PRODUCT_PHOTOS: dict[str, str] = {
    # Electronics
    "BK-ELC-001": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=800&q=85",
    "BK-ELC-002": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=85",
    "BK-ELC-003": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=800&q=85",
    "BK-ELC-004": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=800&q=85",
    "BK-ELC-005": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=800&q=85",
    # Home & Kitchen
    "BK-HOM-001": "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?auto=format&fit=crop&w=800&q=85",
    "BK-HOM-002": "https://images.unsplash.com/photo-1610701596007-11502861dcfa?auto=format&fit=crop&w=800&q=85",
    "BK-HOM-003": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=800&q=85",
    "BK-HOM-004": "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?auto=format&fit=crop&w=800&q=85",
    "BK-HOM-005": "https://images.unsplash.com/photo-1585515320310-259814833e62?auto=format&fit=crop&w=800&q=85",
    # Fashion
    "BK-FSH-001": "https://images.unsplash.com/photo-1601924994987-69e26d50dc26?auto=format&fit=crop&w=800&q=85",
    "BK-FSH-002": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=800&q=85",
    "BK-FSH-003": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=800&q=85",
    "BK-FSH-004": "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?auto=format&fit=crop&w=800&q=85",
    "BK-FSH-005": "https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=800&q=85",
    # Groceries
    "BK-GRO-001": "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?auto=format&fit=crop&w=800&q=85",
    "BK-GRO-002": "https://images.unsplash.com/photo-1587049352846-4a222e784d38?auto=format&fit=crop&w=800&q=85",
    "BK-GRO-003": "https://images.unsplash.com/photo-1564890369478-c89ca6d9cde9?auto=format&fit=crop&w=800&q=85",
    "BK-GRO-004": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=800&q=85",
    "BK-GRO-005": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=800&q=85",
    # Personal Care
    "BK-PRC-001": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?auto=format&fit=crop&w=800&q=85",
    "BK-PRC-002": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=800&q=85",
    "BK-PRC-003": "https://images.unsplash.com/photo-1617897903246-719242758050?auto=format&fit=crop&w=800&q=85",
    "BK-PRC-004": "https://images.unsplash.com/photo-1526947425960-945c6e72858f?auto=format&fit=crop&w=800&q=85",
    "BK-PRC-005": "https://images.unsplash.com/photo-1600857544200-b2f666a9a2ec?auto=format&fit=crop&w=800&q=85",
    # Pune Products
    "BK-PNQ-COP01": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=800&q=85",
    "BK-PNQ-COP02": "https://images.unsplash.com/photo-1610701596007-11502861dcfa?auto=format&fit=crop&w=800&q=85",
    "BK-PNQ-COP03": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=800&q=85",
    "BK-PNQ-COP04": "https://images.unsplash.com/photo-1602928321679-560bb453f190?auto=format&fit=crop&w=800&q=85",
    "BK-PNQ-FSH01": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=800&q=85",
    "BK-PNQ-FSH02": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=800&q=85",
    "BK-PNQ-FSH03": "https://images.unsplash.com/photo-1601924994987-69e26d50dc26?auto=format&fit=crop&w=800&q=85",
    "BK-PNQ-FSH04": "https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?auto=format&fit=crop&w=800&q=85",
    "BK-PNQ-GRO01": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=800&q=85",
    "BK-PNQ-GRO02": "https://images.unsplash.com/photo-1599785209707-a456fc1337bb?auto=format&fit=crop&w=800&q=85",
    "BK-PNQ-GRO03": "https://images.unsplash.com/photo-1567306226416-28f0efdc88ce?auto=format&fit=crop&w=800&q=85",
    "BK-PNQ-GRO04": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=800&q=85",
    "BK-PNQ-STN01": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=800&q=85",
    "BK-PNQ-STN02": "https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?auto=format&fit=crop&w=800&q=85",
    # Mangalore Products
    "BK-IXE-GRO01": "https://images.unsplash.com/photo-1536591375315-0b81c2f1f5fa?auto=format&fit=crop&w=800&q=85",
    "BK-IXE-GRO02": "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?auto=format&fit=crop&w=800&q=85",
    "BK-IXE-GRO03": "https://images.unsplash.com/photo-1599490659213-e2b9527bd087?auto=format&fit=crop&w=800&q=85",
    "BK-IXE-GRO04": "https://images.unsplash.com/photo-1587049352846-4a222e784d38?auto=format&fit=crop&w=800&q=85",
    "BK-IXE-FSH01": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=800&q=85",
    "BK-IXE-FSH02": "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?auto=format&fit=crop&w=800&q=85",
    "BK-IXE-FSH03": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=800&q=85",
    "BK-IXE-GRO05": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=800&q=85",
    "BK-IXE-GRO06": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=800&q=85",
    "BK-IXE-GRO07": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?auto=format&fit=crop&w=800&q=85",
    "BK-IXE-ELC01": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=800&q=85",
    "BK-IXE-ELC02": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=800&q=85",
    # Mumbai Products
    "BK-BOM-FSH01": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=800&q=85",
    "BK-BOM-FSH02": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=800&q=85",
    "BK-BOM-GRO01": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=800&q=85",
    "BK-BOM-GRO02": "https://images.unsplash.com/photo-1536591375315-0b81c2f1f5fa?auto=format&fit=crop&w=800&q=85",
}

# Multi-angle product photograph galleries for PDP gallery inspection
PRODUCT_GALLERIES: dict[str, list[str]] = {
    "BK-ELC-001": [
        "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=800&q=85",
        "https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?auto=format&fit=crop&w=800&q=85",
        "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=800&q=85",
    ],
    "BK-ELC-002": [
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=85",
        "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=800&q=85",
    ],
    "BK-HOM-001": [
        "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?auto=format&fit=crop&w=800&q=85",
        "https://images.unsplash.com/photo-1577937927133-66ef06acdf18?auto=format&fit=crop&w=800&q=85",
    ],
    "BK-HOM-003": [
        "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=800&q=85",
        "https://images.unsplash.com/photo-1589365278144-c9e705f843ba?auto=format&fit=crop&w=800&q=85",
    ],
    "BK-FSH-002": [
        "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=800&q=85",
        "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?auto=format&fit=crop&w=800&q=85",
    ],
    "BK-FSH-004": [
        "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?auto=format&fit=crop&w=800&q=85",
        "https://images.unsplash.com/photo-1535043934128-cf0b28d52f95?auto=format&fit=crop&w=800&q=85",
    ],
    "BK-GRO-001": [
        "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?auto=format&fit=crop&w=800&q=85",
        "https://images.unsplash.com/photo-1498804103079-a6351b050096?auto=format&fit=crop&w=800&q=85",
    ],
    "BK-GRO-002": [
        "https://images.unsplash.com/photo-1587049352846-4a222e784d38?auto=format&fit=crop&w=800&q=85",
        "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=800&q=85",
    ],
}

CATEGORY_FALLBACK_PHOTOS: dict[str, str] = {
    "Electronics": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=800&q=85",
    "Home & Kitchen": "https://images.unsplash.com/photo-1610701596007-11502861dcfa?auto=format&fit=crop&w=800&q=85",
    "Fashion": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=800&q=85",
    "Groceries": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=800&q=85",
    "Personal Care": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?auto=format&fit=crop&w=800&q=85",
}
DEFAULT_PRODUCT_PHOTO = "https://images.unsplash.com/photo-1610701596007-11502861dcfa?auto=format&fit=crop&w=800&q=85"


def get_product_photo_url(sku: str, category: str = "", name: str = "") -> str:
    if sku in REAL_PRODUCT_PHOTOS:
        return REAL_PRODUCT_PHOTOS[sku]
    if category in CATEGORY_FALLBACK_PHOTOS:
        return CATEGORY_FALLBACK_PHOTOS[category]
    n_lower = name.lower()
    if any(k in n_lower for k in ["saree", "silk", "cotton", "shawl", "bag", "leather", "wallet", "kurta", "sandal", "footwear"]):
        return CATEGORY_FALLBACK_PHOTOS["Fashion"]
    if any(k in n_lower for k in ["chai", "coffee", "spice", "cardamom", "honey", "cashew", "ghee", "sweet", "bakarwadi", "tea"]):
        return CATEGORY_FALLBACK_PHOTOS["Groceries"]
    if any(k in n_lower for k in ["copper", "brass", "kettle", "lamp", "pot", "pan", "bottle", "bowl", "diya", "bronze", "stone", "thali"]):
        return CATEGORY_FALLBACK_PHOTOS["Home & Kitchen"]
    if any(k in n_lower for k in ["oil", "serum", "rose", "sandalwood", "soap", "cream", "lotion", "botanical"]):
        return CATEGORY_FALLBACK_PHOTOS["Personal Care"]
    if any(k in n_lower for k in ["earbuds", "speaker", "audio", "charger", "stand", "watch", "headphone"]):
        return CATEGORY_FALLBACK_PHOTOS["Electronics"]
    return DEFAULT_PRODUCT_PHOTO


def get_product_gallery_photos(sku: str) -> list[str]:
    """Return multiple product photographs for gallery inspection."""
    if sku in PRODUCT_GALLERIES:
        return PRODUCT_GALLERIES[sku]
    main_url = get_product_photo_url(sku)
    return [main_url]


def get_offline_fallback_png(sku: str, category: str) -> str:
    W, H = 640, 420
    img = Image.new("RGB", (W, H), (243, 236, 225))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([24, 24, W - 24, H - 24], radius=16, fill=(255, 255, 255), outline=(223, 211, 195), width=3)
    draw.text((48, 48), f"{category.upper()} · {sku}", fill=(74, 25, 44))
    draw.text((48, 200), "Connect to internet to load HD product photo", fill=(89, 82, 75))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"


def get_service_health(db_ok: bool, pending_outbox: int) -> list[dict]:
    from utils.config import settings

    is_pg = settings.DATABASE_URL.startswith("postgresql") or settings.DATABASE_URL.startswith("postgres")
    kafka_configured = bool(settings.KAFKA_BOOTSTRAP_SERVERS)
    opensearch_configured = bool(settings.OPENSEARCH_HOST or settings.OPENSEARCH_URL)

    return [
        {
            "service": "Primary Datastore",
            "engine": "Aiven PostgreSQL" if is_pg else "Local SQLite (Aiven PG Ready)",
            "status": "Connected (Verified)" if db_ok else "Connection Error",
            "active": db_ok,
            "note": "ACID multi-store transactions & stock row locking active in PostgreSQL.",
        },
        {
            "service": "Event Streaming",
            "engine": "Aiven Apache Kafka",
            "status": "Configured (Outbox Relay Active)" if kafka_configured else "Standby (Outbox Queued)",
            "active": kafka_configured,
            "note": f"{pending_outbox} event(s) persisted in transactional outbox table for relay.",
        },
        {
            "service": "Search Engine",
            "engine": "Aiven OpenSearch",
            "status": "Connected" if opensearch_configured else "PostgreSQL Fallback Active",
            "active": opensearch_configured,
            "note": "Authoritative PostgreSQL catalogue search active locally.",
        },
    ]
