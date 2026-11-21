from decimal import Decimal
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.models import City, Customer, Inventory, Product, ProductVariant, Shop, User
from services.auth_service import hash_password
from utils.helpers import get_product_photo_url

logger = logging.getLogger(__name__)

CITIES = [
    {"name": "Bengaluru", "state": "Karnataka", "code": "BLR"},
    {"name": "Mumbai", "state": "Maharashtra", "code": "BOM"},
    {"name": "Pune", "state": "Maharashtra", "code": "PNQ"},
    {"name": "Mangalore", "state": "Karnataka", "code": "IXE"},
]

PARTNER_SHOPS = [
    {
        "shop_code": "SHP-BLR101",
        "shop_name": "Malnad Roasters & Estate Co.",
        "owner_name": "Rohan Hegde",
        "owner_email": "rohan@malnadroasters.in",
        "owner_phone": "9845011223",
        "business_type": "Sole Proprietorship",
        "primary_category": "Groceries",
        "gstin": "29AABCM1234F1Z5",
        "pan_number": "AABCM1234F",
        "fssai_license": "11223344556677",
        "city_code": "BLR",
        "shop_address": "No. 42, 12th Main Road, Indiranagar, Bengaluru",
        "pincode": "560038",
        "pickup_slot": "Morning (9:00 AM – 1:00 PM)",
        "bank_account_holder": "Malnad Roasters",
        "bank_account_number": "50200012345678",
        "bank_ifsc": "HDFC0000184",
        "upi_id": "malnadroasters@okhdfcbank",
        "shop_description": "Specialty Chikmagalur single-estate Arabica coffee roastery and Kodagu spices.",
        "status": "VERIFIED",
    },
    {
        "shop_code": "SHP-BOM204",
        "shop_name": "Kansa & Clay Artisan Studio",
        "owner_name": "Meera Kulkarni",
        "owner_email": "meera@kansaandclay.in",
        "owner_phone": "9820199887",
        "business_type": "Partnership / LLP",
        "primary_category": "Home & Kitchen",
        "gstin": "27AAFCK5678L1Z2",
        "pan_number": "AAFCK5678L",
        "fssai_license": "",
        "city_code": "BOM",
        "shop_address": "Unit 14, Raghuvanshi Mills Compound, Lower Parel, Mumbai",
        "pincode": "400013",
        "pickup_slot": "Afternoon (1:00 PM – 5:00 PM)",
        "bank_account_holder": "Kansa and Clay LLP",
        "bank_account_number": "918020044556677",
        "bank_ifsc": "UTIB0000219",
        "upi_id": "kansaandclay@okaxis",
        "shop_description": "Handcrafted pure brass, copper, and stoneware tableware crafted with Indian artisans.",
        "status": "VERIFIED",
    },
    {
        "shop_code": "SHP-PNQ309",
        "shop_name": "Dakshina Leatherworks",
        "owner_name": "Siddharth Deshmukh",
        "owner_email": "sid@dakshinacraft.in",
        "owner_phone": "9822044556",
        "business_type": "Private Limited",
        "primary_category": "Fashion",
        "gstin": "27AABCD8899P1Z8",
        "pan_number": "AABCD8899P",
        "fssai_license": "",
        "city_code": "PNQ",
        "shop_address": "Lane 6, Koregaon Park, Pune",
        "pincode": "411001",
        "pickup_slot": "Evening (5:00 PM – 9:00 PM)",
        "bank_account_holder": "Dakshina Leatherworks Pvt Ltd",
        "bank_account_number": "003405008899",
        "bank_ifsc": "ICIC0000034",
        "upi_id": "dakshina@okicici",
        "shop_description": "Vegetable-tanned Kolhapuri footwear, everyday bags, and minimalist leather accessories.",
        "status": "VERIFIED",
    },
    {
        "shop_code": "SHP-BLR102",
        "shop_name": "Svara Audio & Electronics",
        "owner_name": "Vikram Sen",
        "owner_email": "vikram@svaraaudio.in",
        "owner_phone": "9845099881",
        "business_type": "Private Limited",
        "primary_category": "Electronics",
        "gstin": "29AABCS8899K1Z4",
        "pan_number": "AABCS8899K",
        "fssai_license": "",
        "city_code": "BLR",
        "shop_address": "15/A, 100 Feet Road, Koramangala 4th Block, Bengaluru",
        "pincode": "560034",
        "pickup_slot": "Afternoon (1:00 PM – 5:00 PM)",
        "bank_account_holder": "Svara Electronics Pvt Ltd",
        "bank_account_number": "004505001122",
        "bank_ifsc": "HDFC0000045",
        "upi_id": "svaraaudio@okhdfcbank",
        "shop_description": "Acoustic gear, ANC earbuds, AMOLED smartwatches, and fast charging docks.",
        "status": "VERIFIED",
    },
    {
        "shop_code": "SHP-IXE401",
        "shop_name": "Aranya Botanical Apothecary",
        "owner_name": "Dr. Shreya Shetty",
        "owner_email": "shreya@aranyabotanicals.in",
        "owner_phone": "9844055667",
        "business_type": "Partnership / LLP",
        "primary_category": "Personal Care",
        "gstin": "29AABCA4433D1Z9",
        "pan_number": "AABCA4433D",
        "fssai_license": "",
        "city_code": "IXE",
        "shop_address": "Heritage Square, Hampankatta, Mangalore",
        "pincode": "575001",
        "pickup_slot": "Morning (9:00 AM – 1:00 PM)",
        "bank_account_holder": "Aranya Botanicals LLP",
        "bank_account_number": "009805003344",
        "bank_ifsc": "SBIN0000871",
        "upi_id": "aranyabotanicals@oksbi",
        "shop_description": "Pure Mysore sandalwood elixirs, steam-distilled rosewater, and Ayurvedic hair therapy oils.",
        "status": "VERIFIED",
    },
]

# Map product categories / SKUs to owning partner shop codes
SKU_TO_SHOP_CODE = {
    # Electronics -> Svara Audio & Electronics (BLR)
    "BK-ELC-001": "SHP-BLR102",
    "BK-ELC-002": "SHP-BLR102",
    "BK-ELC-003": "SHP-BLR102",
    "BK-ELC-004": "SHP-BLR102",
    "BK-ELC-005": "SHP-BLR102",
    # Home & Kitchen -> Kansa & Clay Artisan Studio (BOM)
    "BK-HOM-001": "SHP-BOM204",
    "BK-HOM-002": "SHP-BOM204",
    "BK-HOM-003": "SHP-BOM204",
    "BK-HOM-004": "SHP-BOM204",
    "BK-HOM-005": "SHP-BOM204",
    # Fashion -> Dakshina Leatherworks (PNQ)
    "BK-FSH-001": "SHP-PNQ309",
    "BK-FSH-002": "SHP-PNQ309",
    "BK-FSH-003": "SHP-PNQ309",
    "BK-FSH-004": "SHP-PNQ309",
    "BK-FSH-005": "SHP-PNQ309",
    # Groceries -> Malnad Roasters & Estate Co. (BLR)
    "BK-GRO-001": "SHP-BLR101",
    "BK-GRO-002": "SHP-BLR101",
    "BK-GRO-003": "SHP-BLR101",
    "BK-GRO-004": "SHP-BLR101",
    "BK-GRO-005": "SHP-BLR101",
    # Personal Care -> Aranya Botanical Apothecary (IXE)
    "BK-PRC-001": "SHP-IXE401",
    "BK-PRC-002": "SHP-IXE401",
    "BK-PRC-003": "SHP-IXE401",
    "BK-PRC-004": "SHP-IXE401",
    "BK-PRC-005": "SHP-IXE401",
}

PRODUCTS = [
    {"sku": "BK-ELC-001", "name": "Aether Wireless ANC Earbuds", "brand": "Svara Audio", "category": "Electronics", "description": "11mm dynamic drivers with 38dB active noise cancellation, 32-hour playback case, and IPX5 sweat resistance.", "price": Decimal("1799.00"), "mrp": Decimal("2999.00"), "rating": Decimal("4.75"), "is_featured": True, "stock": {"BLR": 16, "BOM": 11, "PNQ": 9, "IXE": 6}},
    {"sku": "BK-ELC-002", "name": "Chronos Pulse Fitness Smartwatch", "brand": "Vayu Wearables", "category": "Electronics", "description": "1.78-inch AMOLED display with heart-rate & SpO2 tracking, 100+ sports modes, and 8-day battery life.", "price": Decimal("2199.00"), "mrp": Decimal("3499.00"), "rating": Decimal("4.60"), "is_featured": False, "stock": {"BLR": 18, "BOM": 12, "PNQ": 7, "IXE": 8}},
    {"sku": "BK-ELC-003", "name": "Lumix 35W GaN Dual Fast Charger", "brand": "VoltCraft India", "category": "Electronics", "description": "Pocket-sized Gallium Nitride fast charger with USB-C PD & PPS support for smartphones, tablets, and earbuds.", "price": Decimal("899.00"), "mrp": Decimal("1499.00"), "rating": Decimal("4.70"), "is_featured": False, "stock": {"BLR": 25, "BOM": 20, "PNQ": 15, "IXE": 12}},
    {"sku": "BK-ELC-004", "name": "Dhvani Pocket Bluetooth Speaker", "brand": "Svara Audio", "category": "Electronics", "description": "12W rich bass acoustic radiator in a woven fabric shell with 14-hour playtime and built-in mic.", "price": Decimal("1299.00"), "mrp": Decimal("1999.00"), "rating": Decimal("4.65"), "is_featured": False, "stock": {"BLR": 14, "BOM": 10, "PNQ": 8, "IXE": 5}},
    {"sku": "BK-ELC-005", "name": "ErgoTilt Aluminum Laptop Stand", "brand": "DeskCraft", "category": "Electronics", "description": "Foldable anodized aluminum riser with anti-slip silicone pads and ventilated cooling geometry.", "price": Decimal("799.00"), "mrp": Decimal("1299.00"), "rating": Decimal("4.80"), "is_featured": False, "stock": {"BLR": 20, "BOM": 15, "PNQ": 11, "IXE": 9}},

    {"sku": "BK-HOM-001", "name": "Hammered Brass Pour-Over Kettle", "brand": "Kansa & Clay", "category": "Home & Kitchen", "description": "Handcrafted pure brass gooseneck kettle with precision spout and heat-insulated teakwood handle.", "price": Decimal("1299.00"), "mrp": Decimal("1899.00"), "rating": Decimal("4.90"), "is_featured": True, "stock": {"BLR": 12, "BOM": 9, "PNQ": 10, "IXE": 4}},
    {"sku": "BK-HOM-002", "name": "Deccan Stoneware Snack & Bowl Set (6 Pc)", "brand": "Mitti Atelier", "category": "Home & Kitchen", "description": "Matte ivory speckled ceramic bowls and quarter plates fired at 1250°C. Microwave and dishwasher safe.", "price": Decimal("999.00"), "mrp": Decimal("1499.00"), "rating": Decimal("4.75"), "is_featured": False, "stock": {"BLR": 14, "BOM": 11, "PNQ": 8, "IXE": 7}},
    {"sku": "BK-HOM-003", "name": "Pure Copper Hammered Water Bottle (1L)", "brand": "Kansa & Clay", "category": "Home & Kitchen", "description": "Ayurvedic jointless 99.7% pure copper bottle with leak-proof silicone seal and natural lacquer finish.", "price": Decimal("699.00"), "mrp": Decimal("999.00"), "rating": Decimal("4.70"), "is_featured": False, "stock": {"BLR": 22, "BOM": 8, "PNQ": 14, "IXE": 16}},
    {"sku": "BK-HOM-004", "name": "Handloom Cotton Table Runner & Mats", "brand": "Vastra Home", "category": "Home & Kitchen", "description": "Heavyweight 100% organic cotton runner with 4 matching placemats in warm terracotta and ivory weave.", "price": Decimal("649.00"), "mrp": Decimal("950.00"), "rating": Decimal("4.65"), "is_featured": False, "stock": {"BLR": 15, "BOM": 12, "PNQ": 9, "IXE": 10}},
    {"sku": "BK-HOM-005", "name": "Pre-Seasoned Cast Iron Tadka & Skillet Pan", "brand": "Loha Kitchen", "category": "Home & Kitchen", "description": "Naturally non-stick heavy-gauge cast iron pan compatible with gas stoves and induction cooktops.", "price": Decimal("849.00"), "mrp": Decimal("1299.00"), "rating": Decimal("4.85"), "is_featured": False, "stock": {"BLR": 11, "BOM": 9, "PNQ": 6, "IXE": 5}},

    {"sku": "BK-FSH-001", "name": "Handloom Mulberry Silk & Cotton Stole", "brand": "Vastra Heritage", "category": "Fashion", "description": "Woven by master weavers in Karnataka using natural dyes and delicate antique gold zari border detailing.", "price": Decimal("1199.00"), "mrp": Decimal("1799.00"), "rating": Decimal("4.85"), "is_featured": True, "stock": {"BLR": 14, "BOM": 10, "PNQ": 8, "IXE": 11}},
    {"sku": "BK-FSH-002", "name": "Tanned Leather Everyday Crossbody Bag", "brand": "Dakshina Leatherworks", "category": "Fashion", "description": "Hand-burnished cognac genuine leather sling bag with solid antique brass buckles and zippered pockets.", "price": Decimal("1899.00"), "mrp": Decimal("2799.00"), "rating": Decimal("4.72"), "is_featured": False, "stock": {"BLR": 9, "BOM": 11, "PNQ": 6, "IXE": 3}},
    {"sku": "BK-FSH-003", "name": "Khadi Breathable Linen-Cotton Kurta", "brand": "Sutra Looms", "category": "Fashion", "description": "Tailored comfort-fit straight kurta crafted from handspun breathable cotton-linen blend in warm ivory.", "price": Decimal("949.00"), "mrp": Decimal("1399.00"), "rating": Decimal("4.68"), "is_featured": False, "stock": {"BLR": 19, "BOM": 16, "PNQ": 12, "IXE": 14}},
    {"sku": "BK-FSH-004", "name": "Kolhapuri Handcrafted Leather Sandals", "brand": "Dakshina Leatherworks", "category": "Fashion", "description": "Traditional braided vegetable-tanned leather sandals with cushioned footbed for all-day comfort.", "price": Decimal("899.00"), "mrp": Decimal("1299.00"), "rating": Decimal("4.62"), "is_featured": False, "stock": {"BLR": 12, "BOM": 15, "PNQ": 14, "IXE": 7}},
    {"sku": "BK-FSH-005", "name": "Minimalist RFID-Protected Bi-Fold Wallet", "brand": "Dakshina Leatherworks", "category": "Fashion", "description": "Slim full-grain leather wallet with 6 card slots, currency divider, and hidden coin pocket.", "price": Decimal("599.00"), "mrp": Decimal("899.00"), "rating": Decimal("4.78"), "is_featured": False, "stock": {"BLR": 24, "BOM": 19, "PNQ": 15, "IXE": 13}},

    {"sku": "BK-GRO-001", "name": "Chikmagalur Single-Estate Arabica (250g)", "brand": "Malnad Roasters", "category": "Groceries", "description": "Shade-grown AA specialty coffee harvested at 4,200 ft, medium-dark roasted with dark chocolate and almond notes.", "price": Decimal("399.00"), "mrp": Decimal("525.00"), "rating": Decimal("4.92"), "is_featured": True, "stock": {"BLR": 30, "BOM": 22, "PNQ": 18, "IXE": 25}},
    {"sku": "BK-GRO-002", "name": "Coorg Wildflower Raw Forest Honey (500g)", "brand": "Kodagu Naturals", "category": "Groceries", "description": "Unprocessed, cold-extracted multifloral forest honey rich in natural pollen, enzymes, and antioxidants.", "price": Decimal("349.00"), "mrp": Decimal("475.00"), "rating": Decimal("4.80"), "is_featured": False, "stock": {"BLR": 24, "BOM": 18, "PNQ": 14, "IXE": 20}},
    {"sku": "BK-GRO-003", "name": "Assam Orthodox Golden Tips Masala Chai (250g)", "brand": "Nilgiri & Co.", "category": "Groceries", "description": "Whole-leaf second flush Assam tea blended with crushed green cardamom, ginger, clove, and cinnamon.", "price": Decimal("279.00"), "mrp": Decimal("360.00"), "rating": Decimal("4.84"), "is_featured": False, "stock": {"BLR": 28, "BOM": 25, "PNQ": 19, "IXE": 21}},
    {"sku": "BK-GRO-004", "name": "Malabar Tellicherry Black Peppercorns (200g)", "brand": "Kodagu Naturals", "category": "Groceries", "description": "Bold, sun-dried extra-large single-origin peppercorns with high piperine aroma.", "price": Decimal("249.00"), "mrp": Decimal("340.00"), "rating": Decimal("4.76"), "is_featured": False, "stock": {"BLR": 20, "BOM": 17, "PNQ": 13, "IXE": 22}},
    {"sku": "BK-GRO-005", "name": "A2 Gir Cow Cultured Bilona Ghee (500ml)", "brand": "Amrit Farms", "category": "Groceries", "description": "Traditional slow-simmered curd-churned golden ghee packed in a reusable glass jar.", "price": Decimal("699.00"), "mrp": Decimal("850.00"), "rating": Decimal("4.89"), "is_featured": False, "stock": {"BLR": 16, "BOM": 14, "PNQ": 11, "IXE": 12}},

    {"sku": "BK-PRC-001", "name": "Mysore Sandalwood & Vetiver Body Oil", "brand": "Aranya Botanicals", "category": "Personal Care", "description": "Cold-pressed sweet almond and sesame oil infused with steam-distilled sandalwood and root vetiver.", "price": Decimal("549.00"), "mrp": Decimal("750.00"), "rating": Decimal("4.88"), "is_featured": False, "stock": {"BLR": 21, "BOM": 15, "PNQ": 12, "IXE": 18}},
    {"sku": "BK-PRC-002", "name": "Kumkumadi Saffron Radiance Face Serum", "brand": "Aranya Botanicals", "category": "Personal Care", "description": "Classical Ayurvedic night elixir crafted with Kashmiri saffron, manjistha, and lotus extracts.", "price": Decimal("699.00"), "mrp": Decimal("999.00"), "rating": Decimal("4.75"), "is_featured": False, "stock": {"BLR": 14, "BOM": 11, "PNQ": 6, "IXE": 10}},
    {"sku": "BK-PRC-003", "name": "Kannauj Pure Steam-Distilled Rose Water", "brand": "Aranya Botanicals", "category": "Personal Care", "description": "100% pure Damask rose hydrosol facial mist & toner in an amber glass spray bottle.", "price": Decimal("299.00"), "mrp": Decimal("399.00"), "rating": Decimal("4.82"), "is_featured": False, "stock": {"BLR": 26, "BOM": 20, "PNQ": 16, "IXE": 19}},
    {"sku": "BK-PRC-004", "name": "Bhringraj & Amla Scalp Strengthening Oil", "brand": "Keshava Herbals", "category": "Personal Care", "description": "Slow-infused herbal hair oil with hibiscus, curry leaves, and cold-pressed coconut oil.", "price": Decimal("379.00"), "mrp": Decimal("499.00"), "rating": Decimal("4.71"), "is_featured": False, "stock": {"BLR": 22, "BOM": 17, "PNQ": 13, "IXE": 15}},
    {"sku": "BK-PRC-005", "name": "Turmeric & Sandalwood Handmade Soap Trio", "brand": "Aranya Botanicals", "category": "Personal Care", "description": "Cold-processed shea butter bathing bars enriched with Kasturi turmeric and pure sandalwood powder.", "price": Decimal("349.00"), "mrp": Decimal("450.00"), "rating": Decimal("4.79"), "is_featured": False, "stock": {"BLR": 25, "BOM": 19, "PNQ": 14, "IXE": 18}},
]

SAMPLE_VARIANTS = {
    "BK-GRO-001": [
        {"variant_name": "Pack Size", "variant_value": "250g Ground", "price_adjustment": Decimal("0.00"), "stock_quantity": 20},
        {"variant_name": "Pack Size", "variant_value": "500g Whole Bean", "price_adjustment": Decimal("350.00"), "stock_quantity": 15},
    ],
    "BK-FSH-003": [
        {"variant_name": "Size", "variant_value": "Medium (38)", "price_adjustment": Decimal("0.00"), "stock_quantity": 10},
        {"variant_name": "Size", "variant_value": "Large (40)", "price_adjustment": Decimal("0.00"), "stock_quantity": 12},
        {"variant_name": "Size", "variant_value": "X-Large (42)", "price_adjustment": Decimal("50.00"), "stock_quantity": 8},
    ],
    "BK-ELC-001": [
        {"variant_name": "Color", "variant_value": "Obsidian Black", "price_adjustment": Decimal("0.00"), "stock_quantity": 15},
        {"variant_name": "Color", "variant_value": "Ivory White", "price_adjustment": Decimal("0.00"), "stock_quantity": 12},
    ],
    "BK-HOM-003": [
        {"variant_name": "Capacity", "variant_value": "750ml Compact", "price_adjustment": Decimal("-100.00"), "stock_quantity": 10},
        {"variant_name": "Capacity", "variant_value": "1000ml Standard", "price_adjustment": Decimal("0.00"), "stock_quantity": 18},
    ],
}


def seed_initial_data(session: Session) -> None:
    # 1. Seed Cities
    city_map: dict[str, City] = {}
    for c_data in CITIES:
        city = session.execute(select(City).where(City.code == c_data["code"])).scalar_one_or_none()
        if not city:
            city = City(**c_data)
            session.add(city)
            session.flush()
        city_map[city.code] = city

    # 2. Seed Default Admin User
    admin_user = session.execute(select(User).where(User.email == "admin@bharatkart.in")).scalar_one_or_none()
    if not admin_user:
        admin_user = User(
            email="admin@bharatkart.in",
            password_hash=hash_password("Admin@123"),
            role="admin",
            full_name="BharatKart Super Admin",
            phone="9900000001",
            is_active=True,
        )
        session.add(admin_user)
        session.flush()

    # 3. Seed Partner Shops and their Seller Users
    shop_map: dict[str, Shop] = {}
    for s_data in PARTNER_SHOPS:
        seller_email = s_data["owner_email"].lower()
        seller_user = session.execute(select(User).where(User.email == seller_email)).scalar_one_or_none()
        if not seller_user:
            seller_user = User(
                email=seller_email,
                password_hash=hash_password("Seller@123"),
                role="seller",
                full_name=s_data["owner_name"],
                phone=s_data["owner_phone"],
                is_active=True,
            )
            session.add(seller_user)
            session.flush()

        existing_shop = session.execute(select(Shop).where(Shop.shop_code == s_data["shop_code"])).scalar_one_or_none()
        if not existing_shop:
            city = city_map[s_data["city_code"]]
            shop_fields = {k: v for k, v in s_data.items() if k != "city_code"}
            new_shop = Shop(city_id=city.id, user_id=seller_user.id, **shop_fields)
            session.add(new_shop)
            session.flush()
            shop_map[new_shop.shop_code] = new_shop
        else:
            if not existing_shop.user_id:
                existing_shop.user_id = seller_user.id
            shop_map[existing_shop.shop_code] = existing_shop

    # 4. Seed Products with linked Shop IDs
    for p_data in PRODUCTS:
        stock_by_city = p_data["stock"]
        product_fields = {k: v for k, v in p_data.items() if k != "stock"}
        product_fields["image_url"] = get_product_photo_url(p_data["sku"])

        shop_code = SKU_TO_SHOP_CODE.get(p_data["sku"])
        owning_shop = shop_map.get(shop_code)
        if owning_shop:
            product_fields["shop_id"] = owning_shop.id

        product = session.execute(select(Product).where(Product.sku == p_data["sku"])).scalar_one_or_none()
        if not product:
            product = Product(**product_fields)
            session.add(product)
            session.flush()
        else:
            for k, v in product_fields.items():
                setattr(product, k, v)

        # 5. Seed Variants
        if product.sku in SAMPLE_VARIANTS:
            for v_data in SAMPLE_VARIANTS[product.sku]:
                existing_var = session.execute(
                    select(ProductVariant).where(
                        ProductVariant.product_id == product.id,
                        ProductVariant.variant_name == v_data["variant_name"],
                        ProductVariant.variant_value == v_data["variant_value"],
                    )
                ).scalar_one_or_none()
                if not existing_var:
                    session.add(ProductVariant(product_id=product.id, **v_data))

        # 6. Seed Inventories with shop_id
        for city_code, qty in stock_by_city.items():
            city = city_map[city_code]
            inv = session.execute(
                select(Inventory).where(Inventory.city_id == city.id, Inventory.product_id == product.id)
            ).scalar_one_or_none()
            if not inv:
                session.add(
                    Inventory(
                        city_id=city.id,
                        product_id=product.id,
                        shop_id=product.shop_id,
                        stock_quantity=qty,
                    )
                )
            else:
                if not inv.shop_id and product.shop_id:
                    inv.shop_id = product.shop_id

    session.flush()
    logger.info("Demo data seeding completed: 4 cities, 5 partner shops, 25 products, variants, and inventory.")
