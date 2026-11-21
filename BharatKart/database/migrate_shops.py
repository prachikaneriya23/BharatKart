"""
Database Migration Script:
Transform test shops (IDs 6 to 15) into authentic, culturally rich physical stores
for Pune (City 3), Mangalore (City 4), and Mumbai (City 2), with diverse products.
"""
from decimal import Decimal
import os
import sys

sys.path.insert(0, r"C:\Users\prach\Downloads\BharatKart\BharatKart")
os.chdir(r"C:\Users\prach\Downloads\BharatKart\BharatKart")

from backend.database import SessionLocal
from backend.models import City, Inventory, OrderItem, Product, ProductVariant, Shop

session = SessionLocal()

SHOPS_CONFIG = [
    # ── PUNE SHOPS (City 3) ───────────────────────────────────────────────────
    {
        "id": 6,
        "shop_code": "SHP-PNQ310",
        "shop_name": "Tambat Ali Coppersmiths Collective",
        "owner_name": "Dattatray Tambat",
        "owner_email": "dattatray@tambatcopper.in",
        "owner_phone": "9822014589",
        "business_type": "Artisan Guild / Cooperative",
        "primary_category": "Home & Kitchen",
        "pan_number": "AAACT1234F",
        "city_id": 3,  # Pune
        "shop_address": "112 Tambat Ali, Kasba Peth, Pune",
        "pincode": "411011",
        "pickup_slot": "Morning (9:00 AM – 1:00 PM)",
        "bank_account_holder": "Tambat Ali Coppersmiths",
        "bank_account_number": "50100438291032",
        "bank_ifsc": "HDFC0000180",
        "upi_id": "tambatcraft@hdfcbank",
        "shop_description": "Generational heritage coppersmiths crafting authentic hand-hammered pure copper vessels and brassware in historic Kasba Peth.",
        "status": "VERIFIED",
        "products": [
            {
                "sku": "BK-PNQ-COP01",
                "name": "Hand-Hammered Pure Copper Water Pitcher (2.5L)",
                "category": "Home & Kitchen",
                "brand": "Tambat Ali Coppersmiths",
                "description": "Ayurvedic 99.7% pure copper water jug with hand-hammered matha dimple finish crafted in Kasba Peth, Pune.",
                "price": Decimal("1450.00"),
                "mrp": Decimal("1999.00"),
                "rating": Decimal("4.88"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=800&q=85",
                "stock": 25,
            },
            {
                "sku": "BK-PNQ-COP02",
                "name": "Traditional Brass Ganga-Jamuna Urli (12-inch)",
                "category": "Home & Kitchen",
                "brand": "Tambat Ali Coppersmiths",
                "description": "Heavy-gauge dual-tone brass and copper decorative floating flower urli hand-cast by master artisans.",
                "price": Decimal("1890.00"),
                "mrp": Decimal("2600.00"),
                "rating": Decimal("4.92"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1610701596007-11502861dcfa?auto=format&fit=crop&w=800&q=85",
                "stock": 20,
            },
            {
                "sku": "BK-PNQ-COP03",
                "name": "Puneri Pure Bronze Kansa Thali Dining Set",
                "category": "Home & Kitchen",
                "brand": "Tambat Ali Coppersmiths",
                "description": "Certified 78:22 copper-tin bronze thali with katori bowls hand-beaten for wellness dining.",
                "price": Decimal("2490.00"),
                "mrp": Decimal("3400.00"),
                "rating": Decimal("4.95"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=800&q=85",
                "stock": 18,
            },
            {
                "sku": "BK-PNQ-COP04",
                "name": "Hand-Carved Brass Loban Dhoop Burner with Wooden Handle",
                "category": "Home & Kitchen",
                "brand": "Tambat Ali Coppersmiths",
                "description": "Solid brass ritual dhoop and sambrani burner with heat-insulated turned rosewood handle.",
                "price": Decimal("650.00"),
                "mrp": Decimal("950.00"),
                "rating": Decimal("4.80"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1602928321679-560bb453f190?auto=format&fit=crop&w=800&q=85",
                "stock": 30,
            },
        ],
    },
    {
        "id": 7,
        "shop_code": "SHP-PNQ311",
        "shop_name": "Deccan Handloom & Paithani Kendra",
        "owner_name": "Anil Narayan Kshirsagar",
        "owner_email": "anil@deccanpaithani.in",
        "owner_phone": "9822345678",
        "business_type": "Proprietorship",
        "primary_category": "Fashion",
        "pan_number": "ABCPK5678G",
        "city_id": 3,  # Pune
        "shop_address": "342 Laxmi Road, Sadashiv Peth, Pune",
        "pincode": "411030",
        "pickup_slot": "Afternoon (1:00 PM – 5:00 PM)",
        "bank_account_holder": "Deccan Handloom Kendra",
        "bank_account_number": "91202003847291",
        "bank_ifsc": "UTIB0000037",
        "upi_id": "deccanpaithani@axisbank",
        "shop_description": "Specialist Pune boutique celebrating Maharashtra's textile legacy: Yeola Paithani silk, Khun cotton weaves, and handloom drapes.",
        "status": "VERIFIED",
        "products": [
            {
                "sku": "BK-PNQ-FSH01",
                "name": "Authentic Yeola Paithani Pure Silk Stole with Peacock Zari",
                "category": "Fashion",
                "brand": "Deccan Handloom",
                "description": "Handwoven Mulberry silk stole with traditional kaleidoscopic peacock motif woven in real metallic zari.",
                "price": Decimal("2899.00"),
                "mrp": Decimal("3999.00"),
                "rating": Decimal("4.93"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=800&q=85",
                "stock": 15,
            },
            {
                "sku": "BK-PNQ-FSH02",
                "name": "Puneri Traditional Handwoven Khun Cotton Kurta",
                "category": "Fashion",
                "brand": "Deccan Handloom",
                "description": "Breathable handwoven Ilkal and Khun brocade pattern kurta featuring traditional Reshim border.",
                "price": Decimal("1150.00"),
                "mrp": Decimal("1650.00"),
                "rating": Decimal("4.85"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=800&q=85",
                "stock": 25,
            },
            {
                "sku": "BK-PNQ-FSH03",
                "name": "Handloom Tussar Silk Dupatta with Temple Border",
                "category": "Fashion",
                "brand": "Deccan Handloom",
                "description": "Natural wild Tussar silk dupatta hand-dyed in earthy turmeric and madder root hues.",
                "price": Decimal("1650.00"),
                "mrp": Decimal("2200.00"),
                "rating": Decimal("4.87"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1601924994987-69e26d50dc26?auto=format&fit=crop&w=800&q=85",
                "stock": 20,
            },
            {
                "sku": "BK-PNQ-FSH04",
                "name": "Puneri Handloom Cotton Gamcha & Scarf Set",
                "category": "Fashion",
                "brand": "Deccan Handloom",
                "description": "Soft check-weave 100% combed cotton multipurpose traditional gamcha and stole set.",
                "price": Decimal("480.00"),
                "mrp": Decimal("700.00"),
                "rating": Decimal("4.78"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?auto=format&fit=crop&w=800&q=85",
                "stock": 35,
            },
        ],
    },
    {
        "id": 8,
        "shop_code": "SHP-PNQ312",
        "shop_name": "Chitale & Joshi Sweets & Farsan",
        "owner_name": "Mukund Chitale",
        "owner_email": "mukund@chitalejoshi.in",
        "owner_phone": "9822456789",
        "business_type": "Partnership",
        "primary_category": "Groceries",
        "pan_number": "AABCJ9012H",
        "city_id": 3,  # Pune
        "shop_address": "754 Bajirao Road, Shanipar, Pune",
        "pincode": "411002",
        "pickup_slot": "Morning (9:00 AM – 1:00 PM)",
        "bank_account_holder": "Chitale & Joshi Confectioners",
        "bank_account_number": "00291010003948",
        "bank_ifsc": "BKID0000029",
        "upi_id": "chitalesweets@bkid",
        "shop_description": "Iconic Pune snacks, namkeen, and authentic confectioneries prepared using time-honored Maharashtra recipes.",
        "status": "VERIFIED",
        "products": [
            {
                "sku": "BK-PNQ-GRO01",
                "name": "Crunchy Puneri Spiced Bakarwadi (500g Box)",
                "category": "Groceries",
                "brand": "Chitale & Joshi",
                "description": "Spiral crispy flour pastry rolls stuffed with secret toasted poppy, sesame, coconut and dry spice masala.",
                "price": Decimal("220.00"),
                "mrp": Decimal("260.00"),
                "rating": Decimal("4.96"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=800&q=85",
                "stock": 40,
            },
            {
                "sku": "BK-PNQ-GRO02",
                "name": "Pure Alphonso Ratnagiri Mango Barfi (400g)",
                "category": "Groceries",
                "brand": "Chitale & Joshi",
                "description": "Mawa barfi made with real GI-tagged Ratnagiri Hapus mango pulp and pure cow ghee.",
                "price": Decimal("480.00"),
                "mrp": Decimal("580.00"),
                "rating": Decimal("4.91"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1599785209707-a456fc1337bb?auto=format&fit=crop&w=800&q=85",
                "stock": 25,
            },
            {
                "sku": "BK-PNQ-GRO03",
                "name": "Roasted Dagadi Poha Special Chivda (400g)",
                "category": "Groceries",
                "brand": "Chitale & Joshi",
                "description": "Light roasted flattened rice chivda with peanuts, roasted gram, green chillies, and curry leaves.",
                "price": Decimal("190.00"),
                "mrp": Decimal("240.00"),
                "rating": Decimal("4.82"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1567306226416-28f0efdc88ce?auto=format&fit=crop&w=800&q=85",
                "stock": 35,
            },
            {
                "sku": "BK-PNQ-GRO04",
                "name": "Maharashtrian Spiced Goda Masala (250g Jar)",
                "category": "Groceries",
                "brand": "Chitale & Joshi",
                "description": "Aromatic roasted stone flower (dagad phool), coconut and coriander traditional black spice blend.",
                "price": Decimal("210.00"),
                "mrp": Decimal("270.00"),
                "rating": Decimal("4.89"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=800&q=85",
                "stock": 30,
            },
        ],
    },
    {
        "id": 9,
        "shop_code": "SHP-PNQ313",
        "shop_name": "Shaniwar Peth Artisan Stationery",
        "owner_name": "Sunil Shinde",
        "owner_email": "sunil@shaniwarstationery.in",
        "owner_phone": "9822567890",
        "business_type": "Proprietorship",
        "primary_category": "Home & Kitchen",
        "pan_number": "ABCSS3456K",
        "city_id": 3,  # Pune
        "shop_address": "45 Shaniwar Peth, Near Shaniwar Wada, Pune",
        "pincode": "411030",
        "pickup_slot": "Morning (9:00 AM – 1:00 PM)",
        "bank_account_holder": "Shaniwar Peth Stationery",
        "bank_account_number": "20391003847281",
        "bank_ifsc": "SBIN0000455",
        "upi_id": "shindeart@sbi",
        "shop_description": "Handmade cotton rag paper, calligraphic supplies, and wooden desk heirlooms crafted by local Pune bookbinders.",
        "status": "VERIFIED",
        "products": [
            {
                "sku": "BK-PNQ-STN01",
                "name": "Handmade Deckle-Edge Cotton Rag Paper Journal (A5)",
                "category": "Home & Kitchen",
                "brand": "Shaniwar Stationery",
                "description": "Tree-free cotton rag recycled paper journal with vintage leather cord binding and 200 GSM unruled pages.",
                "price": Decimal("599.00"),
                "mrp": Decimal("899.00"),
                "rating": Decimal("4.88"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=800&q=85",
                "stock": 25,
            },
            {
                "sku": "BK-PNQ-STN02",
                "name": "Hand-Turned Sheesham Wood Fountain Pen & Brass Nib",
                "category": "Home & Kitchen",
                "brand": "Shaniwar Stationery",
                "description": "Ergonomic Indian rosewood fountain pen fitted with fine German iridium-tipped brass writing nib.",
                "price": Decimal("850.00"),
                "mrp": Decimal("1200.00"),
                "rating": Decimal("4.83"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?auto=format&fit=crop&w=800&q=85",
                "stock": 20,
            },
        ],
    },
    # ── MANGALORE SHOPS (City 4) ─────────────────────────────────────────────
    {
        "id": 10,
        "shop_code": "SHP-IXE402",
        "shop_name": "Canara Cashew & Confectionery",
        "owner_name": "Ganesh Kamath",
        "owner_email": "ganesh@canaracashew.in",
        "owner_phone": "9845012345",
        "business_type": "Proprietorship",
        "primary_category": "Groceries",
        "pan_number": "ABCKG7890L",
        "city_id": 4,  # Mangalore
        "shop_address": "18 Car Street, Near Venkataramana Temple, Mangalore",
        "pincode": "575001",
        "pickup_slot": "Morning (9:00 AM – 1:00 PM)",
        "bank_account_holder": "Canara Cashew Traders",
        "bank_account_number": "01342010002938",
        "bank_ifsc": "CNRB0000134",
        "upi_id": "canaracashew@cnrb",
        "shop_description": "Renowned Mangalore cashew processor and coastal sweet confectioner serving export-grade dry fruits and coastal delicacies.",
        "status": "VERIFIED",
        "products": [
            {
                "sku": "BK-IXE-GRO01",
                "name": "Mangalore Roasted Jumbo Cashew Nuts W180 Grade (500g)",
                "category": "Groceries",
                "brand": "Canara Cashew",
                "description": "Export-grade Jumbo King W180 whole cashew nuts roasted in pure cow ghee with rock salt.",
                "price": Decimal("650.00"),
                "mrp": Decimal("820.00"),
                "rating": Decimal("4.97"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1536591375315-0b81c2f1f5fa?auto=format&fit=crop&w=800&q=85",
                "stock": 45,
            },
            {
                "sku": "BK-IXE-GRO02",
                "name": "Traditional Ghee Roasted Coastal Macaroons (350g)",
                "category": "Groceries",
                "brand": "Canara Cashew",
                "description": "Crisp melt-in-mouth cone macaroons made from cashew powder, egg whites, and sugar from Car Street.",
                "price": Decimal("280.00"),
                "mrp": Decimal("350.00"),
                "rating": Decimal("4.92"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?auto=format&fit=crop&w=800&q=85",
                "stock": 30,
            },
            {
                "sku": "BK-IXE-GRO03",
                "name": "Crispy Malnad Jackfruit Chips in Coconut Oil (400g)",
                "category": "Groceries",
                "brand": "Canara Cashew",
                "description": "Thin-sliced ripe Halasina Hannu raw jackfruit crisps fried in cold-pressed virgin coconut oil.",
                "price": Decimal("240.00"),
                "mrp": Decimal("300.00"),
                "rating": Decimal("4.85"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1599490659213-e2b9527bd087?auto=format&fit=crop&w=800&q=85",
                "stock": 35,
            },
            {
                "sku": "BK-IXE-GRO04",
                "name": "Organic Palm Jaggery (Karupatti) Cubes (500g)",
                "category": "Groceries",
                "brand": "Canara Cashew",
                "description": "Unrefined coastal palmyra palm jaggery rich in iron, zinc, and natural minerals.",
                "price": Decimal("190.00"),
                "mrp": Decimal("250.00"),
                "rating": Decimal("4.81"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1587049352846-4a222e784d38?auto=format&fit=crop&w=800&q=85",
                "stock": 40,
            },
        ],
    },
    {
        "id": 11,
        "shop_code": "SHP-IXE403",
        "shop_name": "Kudla Coastal Handlooms & Silk",
        "owner_name": "Devadas Poojary",
        "owner_email": "devadas@kudlahandloom.in",
        "owner_phone": "9845123456",
        "business_type": "Weaver Cooperative",
        "primary_category": "Fashion",
        "pan_number": "ABCKP1234M",
        "city_id": 4,  # Mangalore
        "shop_address": "102 Hampankatta Main Road, Mangalore",
        "pincode": "575001",
        "pickup_slot": "Afternoon (1:00 PM – 5:00 PM)",
        "bank_account_holder": "Kudla Handloom Guild",
        "bank_account_number": "10293847561029",
        "bank_ifsc": "KARB0000102",
        "upi_id": "kudlasilk@kbl",
        "shop_description": "Cooperative society of coastal Karnataka weavers offering authentic GI-tagged Udupi handloom sarees, towels, and linen.",
        "status": "VERIFIED",
        "products": [
            {
                "sku": "BK-IXE-FSH01",
                "name": "Authentic Udupi Handloom Cotton Saree with Zari Pallu",
                "category": "Fashion",
                "brand": "Kudla Handlooms",
                "description": "GI-tagged 80-count fine combed cotton drape woven on frame looms with Malpe coastal motifs.",
                "price": Decimal("1750.00"),
                "mrp": Decimal("2400.00"),
                "rating": Decimal("4.94"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=800&q=85",
                "stock": 20,
            },
            {
                "sku": "BK-IXE-FSH02",
                "name": "Coastal Pure Woven Cotton Gamcha & Bath Towel Set (3 Pc)",
                "category": "Fashion",
                "brand": "Kudla Handlooms",
                "description": "High-absorbency natural unbleached waffle-weave coastal cotton bath towels.",
                "price": Decimal("620.00"),
                "mrp": Decimal("850.00"),
                "rating": Decimal("4.82"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?auto=format&fit=crop&w=800&q=85",
                "stock": 35,
            },
            {
                "sku": "BK-IXE-FSH03",
                "name": "Mangalorean Kasuti Embroidered Linen Kurti",
                "category": "Fashion",
                "brand": "Kudla Handlooms",
                "description": "Coastal breathable linen tunic adorned with intricate geometric Karnataka Kasuti needlework.",
                "price": Decimal("1290.00"),
                "mrp": Decimal("1790.00"),
                "rating": Decimal("4.86"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=800&q=85",
                "stock": 25,
            },
        ],
    },
    {
        "id": 12,
        "shop_code": "SHP-IXE404",
        "shop_name": "Netravati Spices & Aromatics",
        "owner_name": "Ibrahim Bawa",
        "owner_email": "ibrahim@netravatispices.in",
        "owner_phone": "9845234567",
        "business_type": "Partnership",
        "primary_category": "Groceries",
        "pan_number": "ABCIB5678N",
        "city_id": 4,  # Mangalore
        "shop_address": "45 Bunder Old Port Road, Mangalore",
        "pincode": "575001",
        "pickup_slot": "Morning (9:00 AM – 1:00 PM)",
        "bank_account_holder": "Netravati Spice Merchants",
        "bank_account_number": "50200039485721",
        "bank_ifsc": "HDFC0000045",
        "upi_id": "netravatispice@hdfcbank",
        "shop_description": "Historic port market spice trader sourcing farm-direct Malabar green cardamom, Byadgi chillies, and Western Ghats kokum.",
        "status": "VERIFIED",
        "products": [
            {
                "sku": "BK-IXE-GRO05",
                "name": "Coorg Green Cardamom Whole Extra Bold 8mm (150g)",
                "category": "Groceries",
                "brand": "Netravati Spices",
                "description": "Sun-dried aromatic whole green cardamom pods sorted for bold 8mm size from Western Ghats plantations.",
                "price": Decimal("520.00"),
                "mrp": Decimal("680.00"),
                "rating": Decimal("4.96"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=800&q=85",
                "stock": 35,
            },
            {
                "sku": "BK-IXE-GRO06",
                "name": "Byadgi Premium Whole Wrinkled Red Chillies (300g)",
                "category": "Groceries",
                "brand": "Netravati Spices",
                "description": "Mild heat deep-red oil-rich Karnataka Byadgi chillies imparting vibrant natural color to curries.",
                "price": Decimal("230.00"),
                "mrp": Decimal("300.00"),
                "rating": Decimal("4.88"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=800&q=85",
                "stock": 40,
            },
            {
                "sku": "BK-IXE-GRO07",
                "name": "Pure Unrefined Western Ghats Kokum Butter (250g Block)",
                "category": "Personal Care",
                "brand": "Netravati Spices",
                "description": "Wild-harvested cold-pressed Garcinia indica butter for natural skin hydration and culinary use.",
                "price": Decimal("380.00"),
                "mrp": Decimal("490.00"),
                "rating": Decimal("4.90"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?auto=format&fit=crop&w=800&q=85",
                "stock": 25,
            },
        ],
    },
    {
        "id": 13,
        "shop_code": "SHP-IXE405",
        "shop_name": "Gerosa Audio & ElectroTech",
        "owner_name": "Ronald D'Souza",
        "owner_email": "ronald@gerosaaudio.in",
        "owner_phone": "9845345678",
        "business_type": "Proprietorship",
        "primary_category": "Electronics",
        "pan_number": "ABCRD9012P",
        "city_id": 4,  # Mangalore
        "shop_address": "88 K.S. Rao Road, Kodialbail, Mangalore",
        "pincode": "575003",
        "pickup_slot": "Evening (5:00 PM – 8:00 PM)",
        "bank_account_holder": "Gerosa Electronics",
        "bank_account_number": "00881000394857",
        "bank_ifsc": "CORP0000088",
        "upi_id": "gerosaaudio@unionbank",
        "shop_description": "Mangalore's premier physical retailer for high-fidelity audio equipment, electrical accessories, and studio gear.",
        "status": "VERIFIED",
        "products": [
            {
                "sku": "BK-IXE-ELC01",
                "name": "Heavy-Duty Spike Guard with Surge Protection & USB (4-Way)",
                "category": "Electronics",
                "brand": "Gerosa Tech",
                "description": "Fire-resistant ABS power strip with 10A surge suppressor, reset circuit breaker, and dual fast-charging USB ports.",
                "price": Decimal("699.00"),
                "mrp": Decimal("999.00"),
                "rating": Decimal("4.85"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=800&q=85",
                "stock": 30,
            },
            {
                "sku": "BK-IXE-ELC02",
                "name": "Acoustic Wood-Finish Bluetooth Bookshelf Speaker (40W)",
                "category": "Electronics",
                "brand": "Gerosa Audio",
                "description": "Handcrafted walnut-grain MDF enclosure bookshelf speaker with deep bass reflex port and Bluetooth 5.3.",
                "price": Decimal("2190.00"),
                "mrp": Decimal("3100.00"),
                "rating": Decimal("4.91"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=800&q=85",
                "stock": 18,
            },
        ],
    },
    # ── MUMBAI SHOPS (City 2) ────────────────────────────────────────────────
    {
        "id": 14,
        "shop_code": "SHP-BOM205",
        "shop_name": "Kala Ghoda Art & Leather Studio",
        "owner_name": "Farhan Merchant",
        "owner_email": "farhan@kalaghodaart.in",
        "owner_phone": "9820123456",
        "business_type": "Partnership",
        "primary_category": "Fashion",
        "pan_number": "ABCFM3456Q",
        "city_id": 2,  # Mumbai
        "shop_address": "24 Ropewalk Lane, Kala Ghoda, Fort, Mumbai",
        "pincode": "400001",
        "pickup_slot": "Afternoon (1:00 PM – 5:00 PM)",
        "bank_account_holder": "Kala Ghoda Studio",
        "bank_account_number": "00141010004928",
        "bank_ifsc": "ICIC0000014",
        "upi_id": "kalaghodacraft@icici",
        "shop_description": "Artisan workshop in South Mumbai's arts precinct creating vegetable-tanned leather messenger bags and canvas luggage.",
        "status": "VERIFIED",
        "products": [
            {
                "sku": "BK-BOM-FSH01",
                "name": "Full-Grain Vegetable-Tanned Leather Briefcase Bag",
                "category": "Fashion",
                "brand": "Kala Ghoda Studio",
                "description": "Solid brass hardware, padded laptop compartment, and burnished saddle leather crafted in Fort, Mumbai.",
                "price": Decimal("3890.00"),
                "mrp": Decimal("5500.00"),
                "rating": Decimal("4.94"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=800&q=85",
                "stock": 12,
            },
            {
                "sku": "BK-BOM-FSH02",
                "name": "Handcrafted Waxed Canvas & Leather Weekender Duffel",
                "category": "Fashion",
                "brand": "Kala Ghoda Studio",
                "description": "Heavy 16oz water-repellent olive canvas duffel with top-grain pull-up leather straps.",
                "price": Decimal("3250.00"),
                "mrp": Decimal("4600.00"),
                "rating": Decimal("4.89"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=800&q=85",
                "stock": 15,
            },
        ],
    },
    {
        "id": 15,
        "shop_code": "SHP-BOM206",
        "shop_name": "Crawford Gourmet & Spice Merchants",
        "owner_name": "Zameer Qureshi",
        "owner_email": "zameer@crawfordspices.in",
        "owner_phone": "9820234567",
        "business_type": "Proprietorship",
        "primary_category": "Groceries",
        "pan_number": "ABCZQ7890R",
        "city_id": 2,  # Mumbai
        "shop_address": "Shop 52, Mahatma Jyotiba Phule Mandai, Fort, Mumbai",
        "pincode": "400001",
        "pickup_slot": "Morning (9:00 AM – 1:00 PM)",
        "bank_account_holder": "Crawford Gourmet",
        "bank_account_number": "00041010003928",
        "bank_ifsc": "HDFC0000004",
        "upi_id": "crawfordspice@hdfcbank",
        "shop_description": "Century-old heritage dry-fruit, saffron, and whole spice purveyors at Mumbai's historic Crawford Market.",
        "status": "VERIFIED",
        "products": [
            {
                "sku": "BK-BOM-GRO01",
                "name": "Kashmir Pure Mongra Saffron Grade 1 (2g)",
                "category": "Groceries",
                "brand": "Crawford Gourmet",
                "description": "Certified Grade-1 all-red saffron stigmas with intense natural crocin aroma from Pampore fields.",
                "price": Decimal("799.00"),
                "mrp": Decimal("1050.00"),
                "rating": Decimal("4.97"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=800&q=85",
                "stock": 30,
            },
            {
                "sku": "BK-BOM-GRO02",
                "name": "California Roasted Salted Pistachios (400g Pouch)",
                "category": "Groceries",
                "brand": "Crawford Gourmet",
                "description": "Naturally opened jumbo pistachios slow-roasted with Himalayan pink crystal salt.",
                "price": Decimal("540.00"),
                "mrp": Decimal("720.00"),
                "rating": Decimal("4.88"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1536591375315-0b81c2f1f5fa?auto=format&fit=crop&w=800&q=85",
                "stock": 35,
            },
        ],
    },
]

try:
    cities = session.query(City).all()

    for cfg in SHOPS_CONFIG:
        shop = session.query(Shop).filter_by(id=cfg["id"]).first()
        if not shop:
            shop = Shop(id=cfg["id"])
            session.add(shop)

        # Update shop attributes
        shop.shop_code = cfg["shop_code"]
        shop.shop_name = cfg["shop_name"]
        shop.owner_name = cfg["owner_name"]
        shop.owner_email = cfg["owner_email"]
        shop.owner_phone = cfg["owner_phone"]
        shop.business_type = cfg["business_type"]
        shop.primary_category = cfg["primary_category"]
        shop.pan_number = cfg["pan_number"]
        shop.city_id = cfg["city_id"]
        shop.shop_address = cfg["shop_address"]
        shop.pincode = cfg["pincode"]
        shop.pickup_slot = cfg["pickup_slot"]
        shop.bank_account_holder = cfg["bank_account_holder"]
        shop.bank_account_number = cfg["bank_account_number"]
        shop.bank_ifsc = cfg["bank_ifsc"]
        shop.upi_id = cfg["upi_id"]
        shop.shop_description = cfg["shop_description"]
        shop.status = cfg["status"]
        session.flush()

        # Delete old duplicate products for this shop (unless referenced by order items)
        old_products = session.query(Product).filter_by(shop_id=shop.id).all()
        for old_p in old_products:
            # Check if referenced in OrderItems
            has_orders = session.query(OrderItem).filter_by(product_id=old_p.id).count() > 0
            if not has_orders:
                session.query(Inventory).filter_by(product_id=old_p.id).delete()
                session.query(ProductVariant).filter_by(product_id=old_p.id).delete()
                session.delete(old_p)
        session.flush()

        # Insert new distinct products
        for pdata in cfg["products"]:
            existing_p = session.query(Product).filter_by(sku=pdata["sku"]).first()
            if not existing_p:
                p = Product(
                    sku=pdata["sku"],
                    name=pdata["name"],
                    brand=pdata["brand"],
                    category=pdata["category"],
                    description=pdata["description"],
                    price=pdata["price"],
                    mrp=pdata["mrp"],
                    rating=pdata["rating"],
                    is_featured=pdata["is_featured"],
                    image_url=pdata["image_url"],
                    shop_id=shop.id,
                )
                session.add(p)
                session.flush()

                # Add inventories across all active cities
                for c in cities:
                    session.add(
                        Inventory(
                            product_id=p.id,
                            city_id=c.id,
                            shop_id=shop.id,
                            stock_quantity=pdata["stock"],
                        )
                    )
            else:
                existing_p.name = pdata["name"]
                existing_p.price = pdata["price"]
                existing_p.mrp = pdata["mrp"]
                existing_p.rating = pdata["rating"]
                existing_p.image_url = pdata["image_url"]
                existing_p.category = pdata["category"]
                existing_p.shop_id = shop.id

    session.commit()
    print("Database migration for Pune, Mangalore, and Mumbai shops completed successfully!")

    # Verify counts
    print("\n=== Shops by City ===")
    for c in cities:
        c_shops = session.query(Shop).filter_by(city_id=c.id).all()
        print(f"\n{c.name} ({len(c_shops)} shops):")
        for s in c_shops:
            prods = session.query(Product).filter_by(shop_id=s.id).all()
            print(f"  • {s.shop_name} ({s.primary_category}) — {len(prods)} products")

except Exception as e:
    session.rollback()
    print(f"ERROR: {e}")
    raise
finally:
    session.close()
