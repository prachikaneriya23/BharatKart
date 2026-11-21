"""
Master Migration Script: Remove All Food Items and Setup Verified Artisan / Retail Stores
"""
from decimal import Decimal
import os
import sys

sys.path.insert(0, r"C:\Users\prach\Downloads\BharatKart\BharatKart")
os.chdir(r"C:\Users\prach\Downloads\BharatKart\BharatKart")

from backend.database import SessionLocal
from backend.models import City, Inventory, OrderItem, Product, ProductVariant, Shop, SubOrder
from sqlalchemy import or_
from utils.helpers import get_product_photo_url

session = SessionLocal()

try:
    cities = session.query(City).all()
    city_map = {c.code: c.id for c in cities}
    all_city_ids = [c.id for c in cities]

    # 1. Shops configuration (15 Verified Non-Food Stores)
    SHOPS_DATA = [
        # BENGALURU (City 1)
        {
            "id": 1,
            "shop_code": "SHP-BLR101",
            "shop_name": "Malnad Craft & Woodwork Co.",
            "owner_name": "Rohan Hegde",
            "owner_email": "rohan@malnadcraft.in",
            "owner_phone": "9845011223",
            "business_type": "Sole Proprietorship",
            "primary_category": "Home & Kitchen",
            "city_id": 1,
            "shop_address": "No. 42, 12th Main Road, Indiranagar, Bengaluru",
            "pincode": "560038",
            "pickup_slot": "Morning (9:00 AM – 1:00 PM)",
            "shop_description": "Heritage Channapatna lacquerware, Mysore rosewood brass inlay carvings, and sandalwood keepsakes.",
            "status": "VERIFIED",
            "products": [
                {
                    "sku": "BK-WDC-001",
                    "name": "Handcrafted Channapatna Lacquer Wooden Toy & Figurine Set",
                    "category": "Home & Kitchen",
                    "brand": "Malnad Woodcraft",
                    "description": "Vegetable-dyed non-toxic turned Wrightia tinctoria wooden figurine set handcrafted by master artisans in Channapatna.",
                    "price": Decimal("799.00"),
                    "mrp": Decimal("1199.00"),
                    "rating": Decimal("4.88"),
                    "is_featured": True,
                    "image_url": "https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?auto=format&fit=crop&w=800&q=85",
                    "stock": 35,
                },
                {
                    "sku": "BK-WDC-002",
                    "name": "Mysore Pure Rosewood Brass-Inlay Coaster Set (6 Pc)",
                    "category": "Home & Kitchen",
                    "brand": "Malnad Woodcraft",
                    "description": "Hand-burnished seasoned dark rosewood drink coasters with traditional floral solid brass inlay detailing.",
                    "price": Decimal("649.00"),
                    "mrp": Decimal("950.00"),
                    "rating": Decimal("4.82"),
                    "is_featured": False,
                    "image_url": "https://images.unsplash.com/photo-1615529182904-14819c35db37?auto=format&fit=crop&w=800&q=85",
                    "stock": 28,
                },
                {
                    "sku": "BK-WDC-003",
                    "name": "Hand-Carved Sandalwood Fragrant Jali Keepsake Box",
                    "category": "Home & Kitchen",
                    "brand": "Malnad Woodcraft",
                    "description": "Intricate openwork jali carving crafted from authentic fragrant sandalwood for jewelry and treasured keepsakes.",
                    "price": Decimal("1299.00"),
                    "mrp": Decimal("1850.00"),
                    "rating": Decimal("4.92"),
                    "is_featured": True,
                    "image_url": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=800&q=85",
                    "stock": 20,
                },
                {
                    "sku": "BK-WDC-004",
                    "name": "Solid Sheesham Wooden Wall Clock with Roman Numerals",
                    "category": "Home & Kitchen",
                    "brand": "Malnad Woodcraft",
                    "description": "Natural grain 12-inch rustic round wall clock with silent sweep Japanese quartz movement and brass hands.",
                    "price": Decimal("1499.00"),
                    "mrp": Decimal("2100.00"),
                    "rating": Decimal("4.79"),
                    "is_featured": False,
                    "image_url": "https://images.unsplash.com/photo-1563861826100-9cb868fdbe1c?auto=format&fit=crop&w=800&q=85",
                    "stock": 22,
                },
                {
                    "sku": "BK-WDC-005",
                    "name": "Bidriware Silver-Inlaid Metal Trinket Dish",
                    "category": "Home & Kitchen",
                    "brand": "Malnad Woodcraft",
                    "description": "Certified Karnataka GI-tagged Bidriware blackened zinc-copper alloy dish hand-inlaid with 99.9% pure silver wire.",
                    "price": Decimal("899.00"),
                    "mrp": Decimal("1250.00"),
                    "rating": Decimal("4.85"),
                    "is_featured": False,
                    "image_url": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=800&q=85",
                    "stock": 25,
                },
            ],
        },
        # PUNE (City 3) - Shop 8 replaces Chitale & Joshi Sweets
        {
            "id": 8,
            "shop_code": "SHP-PNQ312",
            "shop_name": "Sinhagad Handcrafted Terracotta & Pottery",
            "owner_name": "Ganesh Joshi",
            "owner_email": "ganesh@sinhagadpottery.in",
            "owner_phone": "9822045612",
            "business_type": "Artisan Guild / Cooperative",
            "primary_category": "Home & Kitchen",
            "city_id": 3,
            "shop_address": "450 Bajirao Road, Sadashiv Peth, Pune",
            "pincode": "411030",
            "pickup_slot": "Morning (9:00 AM – 1:00 PM)",
            "shop_description": "Natural red-clay water vessels, Warli hand-painted vases, and glazed stoneware pottery shaped by Pune ceramic artists.",
            "status": "VERIFIED",
            "products": [
                {
                    "sku": "BK-TER-001",
                    "name": "Handcrafted Unglazed Terracotta Water Matka Dispenser (5L)",
                    "category": "Home & Kitchen",
                    "brand": "Sinhagad Pottery",
                    "description": "Natural porous clay water container with solid food-grade brass tap for mineral-rich Ayurvedic natural cooling.",
                    "price": Decimal("749.00"),
                    "mrp": Decimal("1050.00"),
                    "rating": Decimal("4.92"),
                    "is_featured": True,
                    "image_url": "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?auto=format&fit=crop&w=800&q=85",
                    "stock": 30,
                },
                {
                    "sku": "BK-TER-002",
                    "name": "Artisan Studio Matte Ceramic Planter & Saucer Set",
                    "category": "Home & Kitchen",
                    "brand": "Sinhagad Pottery",
                    "description": "High-fired speckled stoneware indoor succulent and tabletop planter with drainage hole and glazed matching saucer.",
                    "price": Decimal("599.00"),
                    "mrp": Decimal("850.00"),
                    "rating": Decimal("4.80"),
                    "is_featured": False,
                    "image_url": "https://images.unsplash.com/photo-1485955900006-10f4d324d411?auto=format&fit=crop&w=800&q=85",
                    "stock": 25,
                },
                {
                    "sku": "BK-TER-003",
                    "name": "Hand-Painted Warli Art Terracotta Tabletop Vase",
                    "category": "Home & Kitchen",
                    "brand": "Sinhagad Pottery",
                    "description": "Terracotta flared bottleneck floral vase hand-painted in traditional Maharashtrian Warli tribal art motifs.",
                    "price": Decimal("699.00"),
                    "mrp": Decimal("950.00"),
                    "rating": Decimal("4.85"),
                    "is_featured": False,
                    "image_url": "https://images.unsplash.com/photo-1581783342308-f792dbdd27c5?auto=format&fit=crop&w=800&q=85",
                    "stock": 28,
                },
                {
                    "sku": "BK-TER-004",
                    "name": "Earthen Clay Cooking Handi Pot with Lid (2.5L)",
                    "category": "Home & Kitchen",
                    "brand": "Sinhagad Pottery",
                    "description": "Slow-cooking unglazed natural terracotta deep handi for authentic aroma and even alkaline heat distribution.",
                    "price": Decimal("499.00"),
                    "mrp": Decimal("750.00"),
                    "rating": Decimal("4.82"),
                    "is_featured": False,
                    "image_url": "https://images.unsplash.com/photo-1590736704728-f4730bb30770?auto=format&fit=crop&w=800&q=85",
                    "stock": 32,
                },
            ],
        },
        # MANGALORE (City 4) - Shop 10 replaces Canara Cashews
        {
            "id": 10,
            "shop_code": "SHP-IXE402",
            "shop_name": "Canara Coastal Crafts & Bamboo Studio",
            "owner_name": "Devadas Prabhu",
            "owner_email": "devadas@canaracrafts.in",
            "owner_phone": "9845234190",
            "business_type": "Sole Proprietorship",
            "primary_category": "Home & Kitchen",
            "city_id": 4,
            "shop_address": "88 KS Rao Road, Kodialbail, Mangalore",
            "pincode": "575003",
            "pickup_slot": "Morning (9:00 AM – 1:00 PM)",
            "shop_description": "Mother-of-pearl jewelry boxes, coastal bamboo cane weaves, and hand-polished coconut shell dining bowls.",
            "status": "VERIFIED",
            "products": [
                {
                    "sku": "BK-CAN-001",
                    "name": "Natural Pearl-Oyster Shell Inlay Keepsake Jewelry Box",
                    "category": "Home & Kitchen",
                    "brand": "Canara Coastal Crafts",
                    "description": "Velvet-lined wooden jewelry organizer handcrafted with iridescent sea-shell mosaic tiles by Karavali artisans.",
                    "price": Decimal("950.00"),
                    "mrp": Decimal("1350.00"),
                    "rating": Decimal("4.93"),
                    "is_featured": True,
                    "image_url": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=800&q=85",
                    "stock": 25,
                },
                {
                    "sku": "BK-CAN-002",
                    "name": "Handwoven Coastal Golden Cane & Bamboo Fruit Basket",
                    "category": "Home & Kitchen",
                    "brand": "Canara Coastal Crafts",
                    "description": "Sturdy natural cane openwork bread and fruit basket handcrafted using seasoned riverine bamboo fibers.",
                    "price": Decimal("420.00"),
                    "mrp": Decimal("600.00"),
                    "rating": Decimal("4.76"),
                    "is_featured": False,
                    "image_url": "https://images.unsplash.com/photo-1595079672139-5470805086ae?auto=format&fit=crop&w=800&q=85",
                    "stock": 35,
                },
                {
                    "sku": "BK-CAN-003",
                    "name": "Eco-Friendly Natural Coconut Shell Serving Bowl Set (4 Pc)",
                    "category": "Home & Kitchen",
                    "brand": "Canara Coastal Crafts",
                    "description": "Smooth organic reclaimed coconut shells hand-polished with pure coconut oil for artisanal sustainable dining.",
                    "price": Decimal("550.00"),
                    "mrp": Decimal("780.00"),
                    "rating": Decimal("4.81"),
                    "is_featured": False,
                    "image_url": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=800&q=85",
                    "stock": 30,
                },
                {
                    "sku": "BK-CAN-004",
                    "name": "Hand-Braided Coastal Coir Fiber Welcome Door Mat",
                    "category": "Home & Kitchen",
                    "brand": "Canara Coastal Crafts",
                    "description": "Heavyweight natural coconut coir outdoor mat with non-slip recycled rubber backing and embossed geometric border.",
                    "price": Decimal("380.00"),
                    "mrp": Decimal("550.00"),
                    "rating": Decimal("4.73"),
                    "is_featured": False,
                    "image_url": "https://images.unsplash.com/photo-1582533561751-ef6f6ab93a2e?auto=format&fit=crop&w=800&q=85",
                    "stock": 40,
                },
            ],
        },
        # MANGALORE (City 4) - Shop 12 replaces Netravati Spices
        {
            "id": 12,
            "shop_code": "SHP-IXE404",
            "shop_name": "Pilikutla Heritage Bell Metal & Woodcraft",
            "owner_name": "Sudhakar Poojary",
            "owner_email": "sudhakar@pilikutlacraft.in",
            "owner_phone": "9845671234",
            "business_type": "Artisan Cooperative",
            "primary_category": "Home & Kitchen",
            "city_id": 4,
            "shop_address": "12 Bunder Port Road, Old Port, Mangalore",
            "pincode": "575001",
            "pickup_slot": "Morning (9:00 AM – 1:00 PM)",
            "shop_description": "Karavali bronze temple lamps, brass cast oil diyas, and authentic hand-carved coastal teakwood artifacts.",
            "status": "VERIFIED",
            "products": [
                {
                    "sku": "BK-KBL-001",
                    "name": "Traditional Karavali Bell Metal Temple Lamp (Kuthu Vilakku 14-inch)",
                    "category": "Home & Kitchen",
                    "brand": "Pilikutla Heritage",
                    "description": "Solid heavy-cast traditional bell-metal peacock thooku vilakku oil lamp for festive living room and puja mandir decor.",
                    "price": Decimal("1650.00"),
                    "mrp": Decimal("2300.00"),
                    "rating": Decimal("4.96"),
                    "is_featured": True,
                    "image_url": "https://images.unsplash.com/photo-1606293926075-69a00dbfde81?auto=format&fit=crop&w=800&q=85",
                    "stock": 22,
                },
                {
                    "sku": "BK-KBL-002",
                    "name": "Hand-Carved Teakwood Yakshagana Cultural Wall Mask",
                    "category": "Home & Kitchen",
                    "brand": "Pilikutla Heritage",
                    "description": "Authentic coastal Karnataka Yakshagana crown motif intricately chiseled from single-piece aged teakwood.",
                    "price": Decimal("1450.00"),
                    "mrp": Decimal("2100.00"),
                    "rating": Decimal("4.91"),
                    "is_featured": True,
                    "image_url": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=800&q=85",
                    "stock": 18,
                },
                {
                    "sku": "BK-KBL-003",
                    "name": "Cast Bronze Singing Healing Meditation Bowl with Mallet",
                    "category": "Home & Kitchen",
                    "brand": "Pilikutla Heritage",
                    "description": "Pure 7-metal Tibetan bell alloy bowl producing resonant sustained harmonics for mindfulness and relaxation.",
                    "price": Decimal("1290.00"),
                    "mrp": Decimal("1800.00"),
                    "rating": Decimal("4.87"),
                    "is_featured": False,
                    "image_url": "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=800&q=85",
                    "stock": 25,
                },
            ],
        },
        # MUMBAI (City 2) - Shop 15 replaces Crawford Gourmet
        {
            "id": 15,
            "shop_code": "SHP-BOM206",
            "shop_name": "Bombay Heritage Brass & Lighting Studio",
            "owner_name": "Farhan Merchant",
            "owner_email": "farhan@bombayheritage.in",
            "owner_phone": "9820567890",
            "business_type": "Private Limited",
            "primary_category": "Home & Kitchen",
            "city_id": 2,
            "shop_address": "82 Lokmanya Tilak Road, Crawford Market, Mumbai",
            "pincode": "400001",
            "pickup_slot": "Evening (5:00 PM – 9:00 PM)",
            "shop_description": "Architectural brass pendant lights, filigree Moroccan lanterns, and hand-beaten warm candlelight sconces.",
            "status": "VERIFIED",
            "products": [
                {
                    "sku": "BK-LGT-001",
                    "name": "Moradabad Antique Brass Filigree Hanging Lantern (16-inch)",
                    "category": "Home & Kitchen",
                    "brand": "Bombay Heritage",
                    "description": "Perforated intricate brass hanging light creating warm patterned shadows with adjustable antique chain link.",
                    "price": Decimal("1750.00"),
                    "mrp": Decimal("2500.00"),
                    "rating": Decimal("4.94"),
                    "is_featured": True,
                    "image_url": "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?auto=format&fit=crop&w=800&q=85",
                    "stock": 25,
                },
                {
                    "sku": "BK-LGT-002",
                    "name": "Hand-Beaten Brass Moroccan Floor Candle Lantern",
                    "category": "Home & Kitchen",
                    "brand": "Bombay Heritage",
                    "description": "Pyramidal brass and beveled glass lantern with ventilated top dome and secure latch for pillar candles.",
                    "price": Decimal("1250.00"),
                    "mrp": Decimal("1799.00"),
                    "rating": Decimal("4.88"),
                    "is_featured": False,
                    "image_url": "https://images.unsplash.com/photo-1540932239986-30128078f3c5?auto=format&fit=crop&w=800&q=85",
                    "stock": 30,
                },
            ],
        },
    ]

    # Clean up test shop 16 and test duplicate items from shop 4
    session.query(Inventory).filter(Inventory.shop_id == 16).delete()
    session.query(ProductVariant).filter(ProductVariant.product_id.in_(
        session.query(Product.id).filter(Product.shop_id == 16)
    )).delete(synchronize_session=False)
    session.query(Product).filter(Product.shop_id == 16).delete()
    session.query(Shop).filter(Shop.id == 16).delete()

    # Clean up random test products from shop 4 (keep only BK-ELC-*)
    test_pids = [p.id for p in session.query(Product).filter(Product.shop_id == 4, ~Product.sku.startswith("BK-ELC-")).all()]
    if test_pids:
        session.query(Inventory).filter(Inventory.product_id.in_(test_pids)).delete(synchronize_session=False)
        session.query(ProductVariant).filter(ProductVariant.product_id.in_(test_pids)).delete(synchronize_session=False)
        session.query(Product).filter(Product.id.in_(test_pids)).delete(synchronize_session=False)

    # Clean up old food items from existing shops (BK-GRO-*, BK-PNQ-GRO*, BK-IXE-GRO*, BK-BOM-GRO*)
    food_pids = [p.id for p in session.query(Product).filter(
        or_(
            Product.category == "Groceries",
            Product.sku.like("%GRO%"),
        )
    ).all()]
    if food_pids:
        session.query(Inventory).filter(Inventory.product_id.in_(food_pids)).delete(synchronize_session=False)
        session.query(ProductVariant).filter(ProductVariant.product_id.in_(food_pids)).delete(synchronize_session=False)
        session.query(Product).filter(Product.id.in_(food_pids)).delete(synchronize_session=False)
        print(f"Removed {len(food_pids)} old food products.")

    # Apply updated non-food shops & their products
    for s_info in SHOPS_DATA:
        s_id = s_info["id"]
        shop = session.query(Shop).filter(Shop.id == s_id).first()
        if shop:
            shop.shop_code = s_info["shop_code"]
            shop.shop_name = s_info["shop_name"]
            shop.owner_name = s_info["owner_name"]
            shop.owner_email = s_info["owner_email"]
            shop.owner_phone = s_info["owner_phone"]
            shop.business_type = s_info["business_type"]
            shop.primary_category = s_info["primary_category"]
            shop.city_id = s_info["city_id"]
            shop.shop_address = s_info["shop_address"]
            shop.pincode = s_info["pincode"]
            shop.pickup_slot = s_info["pickup_slot"]
            shop.shop_description = s_info["shop_description"]
            shop.status = s_info["status"]
            session.flush()

        # Seed new non-food products
        for p_info in s_info["products"]:
            sku = p_info["sku"]
            prod = session.query(Product).filter(Product.sku == sku).first()
            if not prod:
                prod = Product(
                    sku=sku,
                    name=p_info["name"],
                    brand=p_info["brand"],
                    category=p_info["category"],
                    description=p_info["description"],
                    price=p_info["price"],
                    mrp=p_info["mrp"],
                    rating=p_info["rating"],
                    is_featured=p_info["is_featured"],
                    image_url=p_info["image_url"],
                    shop_id=s_id,
                )
                session.add(prod)
                session.flush()
            else:
                prod.name = p_info["name"]
                prod.brand = p_info["brand"]
                prod.category = p_info["category"]
                prod.description = p_info["description"]
                prod.price = p_info["price"]
                prod.mrp = p_info["mrp"]
                prod.rating = p_info["rating"]
                prod.is_featured = p_info["is_featured"]
                prod.image_url = p_info["image_url"]
                prod.shop_id = s_id
                session.flush()

            # Seed inventory across all cities
            for cid in all_city_ids:
                inv = session.query(Inventory).filter(Inventory.product_id == prod.id, Inventory.city_id == cid).first()
                if not inv:
                    session.add(Inventory(
                        product_id=prod.id,
                        city_id=cid,
                        shop_id=s_id,
                        stock_quantity=p_info["stock"],
                    ))
                else:
                    inv.shop_id = s_id
                    if inv.stock_quantity <= 0:
                        inv.stock_quantity = p_info["stock"]

    # Also update Deccan Handloom & Paithani Kendra (Shop 7) to have authentic Saree catalog:
    s7_sarees = [
        {
            "sku": "BK-PNQ-FSH01",
            "name": "Authentic Yeola Paithani Pure Silk Saree with Peacock Zari",
            "category": "Fashion",
            "brand": "Deccan Handloom",
            "description": "100% pure mulberry silk handwoven 6-yard Paithani saree with authentic Maharani peacock pallu in pure gold zari.",
            "price": Decimal("4850.00"),
            "mrp": Decimal("6500.00"),
            "rating": Decimal("4.95"),
            "is_featured": True,
            "image_url": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=800&q=85",
            "stock": 18,
        },
        {
            "sku": "BK-PNQ-FSH02",
            "name": "Traditional Nauvari Handloom Cotton Saree (9 Yards)",
            "category": "Fashion",
            "brand": "Deccan Handloom",
            "description": "Authentic Maharashtrian 9-yard Nauvari kashta handloom saree in breathable combed cotton with contrasting temple border.",
            "price": Decimal("1650.00"),
            "mrp": Decimal("2200.00"),
            "rating": Decimal("4.90"),
            "is_featured": True,
            "image_url": "https://images.unsplash.com/photo-1609357605129-26f69add5d6e?auto=format&fit=crop&w=800&q=85",
            "stock": 25,
        },
        {
            "sku": "BK-PNQ-FSH03",
            "name": "Handloom Tussar Silk Saree with Antique Gold Border",
            "category": "Fashion",
            "brand": "Deccan Handloom",
            "description": "Wild forest Tussar raw silk festive drape adorned with subtle antique zari buttas and hand-twisted tassels.",
            "price": Decimal("2890.00"),
            "mrp": Decimal("3900.00"),
            "rating": Decimal("4.92"),
            "is_featured": False,
            "image_url": "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?auto=format&fit=crop&w=800&q=85",
            "stock": 20,
        },
        {
            "sku": "BK-PNQ-FSH04",
            "name": "Peshwai Zari Border Pure Silk Dupatta & Stole",
            "category": "Fashion",
            "brand": "Deccan Handloom",
            "description": "Opulent 2.5m festive handwoven silk dupatta with intricate gold brocade border for ethnic occasions.",
            "price": Decimal("1250.00"),
            "mrp": Decimal("1750.00"),
            "rating": Decimal("4.86"),
            "is_featured": False,
            "image_url": "https://images.unsplash.com/photo-1601924994987-69e26d50dc26?auto=format&fit=crop&w=800&q=85",
            "stock": 28,
        },
    ]
    for s_item in s7_sarees:
        sku = s_item["sku"]
        prod = session.query(Product).filter(Product.sku == sku).first()
        if not prod:
            prod = Product(sku=sku, name=s_item["name"], brand=s_item["brand"], category=s_item["category"],
                           description=s_item["description"], price=s_item["price"], mrp=s_item["mrp"],
                           rating=s_item["rating"], is_featured=s_item["is_featured"], image_url=s_item["image_url"], shop_id=7)
            session.add(prod)
            session.flush()
        else:
            prod.name = s_item["name"]
            prod.brand = s_item["brand"]
            prod.category = s_item["category"]
            prod.description = s_item["description"]
            prod.price = s_item["price"]
            prod.mrp = s_item["mrp"]
            prod.rating = s_item["rating"]
            prod.is_featured = s_item["is_featured"]
            prod.image_url = s_item["image_url"]
            prod.shop_id = 7
            session.flush()
        for cid in all_city_ids:
            inv = session.query(Inventory).filter(Inventory.product_id == prod.id, Inventory.city_id == cid).first()
            if not inv:
                session.add(Inventory(product_id=prod.id, city_id=cid, shop_id=7, stock_quantity=s_item["stock"]))
            else:
                inv.shop_id = 7
                if inv.stock_quantity <= 0:
                    inv.stock_quantity = s_item["stock"]

    # Also update Kudla Coastal Handlooms (Shop 11) to have authentic coastal sarees:
    s11_sarees = [
        {
            "sku": "BK-IXE-FSH01",
            "name": "Authentic Udupi Handloom Cotton Saree with Zari Pallu",
            "category": "Fashion",
            "brand": "Kudla Coastal Handlooms",
            "description": "GI-tagged 80s combed pure cotton saree with contrasting dye border and handwoven gold zari pallu.",
            "price": Decimal("1850.00"),
            "mrp": Decimal("2450.00"),
            "rating": Decimal("4.94"),
            "is_featured": True,
            "image_url": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=800&q=85",
            "stock": 25,
        },
        {
            "sku": "BK-IXE-FSH02",
            "name": "Traditional Coastal Kasavu Gold Tissue Festive Saree",
            "category": "Fashion",
            "brand": "Kudla Coastal Handlooms",
            "description": "Lightweight ivory tissue saree with 3-inch fine antique gold zari border and hand-spun tassels.",
            "price": Decimal("2150.00"),
            "mrp": Decimal("2890.00"),
            "rating": Decimal("4.91"),
            "is_featured": True,
            "image_url": "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?auto=format&fit=crop&w=800&q=85",
            "stock": 22,
        },
        {
            "sku": "BK-IXE-FSH03",
            "name": "Mangalorean Handwoven Silk & Cotton Festive Stole",
            "category": "Fashion",
            "brand": "Kudla Coastal Handlooms",
            "description": "Artisan woven handloom cotton-silk dupatta in soothing coastal indigo with delicate mirror work accents.",
            "price": Decimal("890.00"),
            "mrp": Decimal("1250.00"),
            "rating": Decimal("4.85"),
            "is_featured": False,
            "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=800&q=85",
            "stock": 30,
        },
    ]
    for s_item in s11_sarees:
        sku = s_item["sku"]
        prod = session.query(Product).filter(Product.sku == sku).first()
        if not prod:
            prod = Product(sku=sku, name=s_item["name"], brand=s_item["brand"], category=s_item["category"],
                           description=s_item["description"], price=s_item["price"], mrp=s_item["mrp"],
                           rating=s_item["rating"], is_featured=s_item["is_featured"], image_url=s_item["image_url"], shop_id=11)
            session.add(prod)
            session.flush()
        else:
            prod.name = s_item["name"]
            prod.brand = s_item["brand"]
            prod.category = s_item["category"]
            prod.description = s_item["description"]
            prod.price = s_item["price"]
            prod.mrp = s_item["mrp"]
            prod.rating = s_item["rating"]
            prod.is_featured = s_item["is_featured"]
            prod.image_url = s_item["image_url"]
            prod.shop_id = 11
            session.flush()
        for cid in all_city_ids:
            inv = session.query(Inventory).filter(Inventory.product_id == prod.id, Inventory.city_id == cid).first()
            if not inv:
                session.add(Inventory(product_id=prod.id, city_id=cid, shop_id=11, stock_quantity=s_item["stock"]))
            else:
                inv.shop_id = 11
                if inv.stock_quantity <= 0:
                    inv.stock_quantity = s_item["stock"]

    session.commit()
    print("Migration successful: all food items removed, authentic non-food stores configured across all 4 cities.")

except Exception as e:
    session.rollback()
    print(f"Error during migration: {e}")
    raise
finally:
    session.close()
