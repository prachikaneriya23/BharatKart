# 🇮🇳 BharatKart — Hyperlocal Multi-Store Marketplace

**One marketplace. Multiple local stores. One seamless shopping experience.**

BharatKart is a hyperlocal e-commerce platform designed to connect customers with nearby physical retail stores. It brings multiple local shops into one digital marketplace, allowing customers to explore products, compare prices, manage a combined shopping cart, and place orders conveniently.

The platform also provides dedicated seller and administrative workflows to support local businesses and marketplace operations.

---

## ✨ Key Features

### 🛍️ Customer Experience
- Customer registration and authentication.
- City-based local store discovery.
- Browse products across multiple physical retail stores.
- Individual shop storefronts and product catalogues.
- Product details, images, pricing, variants, and stock information.
- Add products from multiple shops to a single shopping cart.
- Shop-wise cart organization and order summaries.
- Unified checkout experience.
- Order confirmation and order management.

### 🏪 Seller Portal
- Seller registration and shop onboarding.
- Seller approval workflow.
- Manage individual shop details.
- Add, update, and manage product listings.
- Manage product variants, pricing, and inventory.
- View and manage shop orders.
- Shop-specific access and ownership controls.

### ⚙️ Admin & Operations
- Seller and shop approval management.
- Customer and shop oversight.
- Product and inventory management.
- Parent orders and shop-wise suborders.
- Marketplace operations dashboard.
- Event and order monitoring.

### 🤖 Shopping Intelligence Assistant
- Product and store discovery assistance.
- Product search and recommendations.
- Cross-store product comparison.
- Smart multi-store basket optimization.
- Budget-aware shopping suggestions.
- Stock-aware alternatives.
- Rule-based fallback functionality when an external AI API is unavailable.

---

## 🧠 Smart Multi-Store Basket Optimization

BharatKart is designed to make multi-store shopping more convenient.

The shopping assistant can help customers:
- Compare product prices across available stores.
- Find cost-effective shopping combinations.
- Optimize a basket based on a specified budget.
- Consider the trade-off between lower prices and fewer store visits.
- Explore alternatives when products are unavailable.

---

## 🏗️ Technology Stack

| Category | Technologies |
|---|---|
| Frontend & Application | Python, Streamlit |
| Backend | Python |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Data Validation | Pydantic |
| Event Streaming | Apache Kafka |
| Search Engine | OpenSearch |
| AI Integration | Google Gemini API (optional) |
| Image Processing | Pillow |
| Data Handling | Pandas |
| Testing | Pytest |
| Deployment Configuration | Streamlit |

### Aiven Cloud Infrastructure

BharatKart is designed to integrate with Aiven-managed services:

- **Aiven PostgreSQL:** Primary relational database.
- **Aiven Apache Kafka:** Event streaming and asynchronous event processing.
- **Aiven OpenSearch:** Product search and indexing.

Kafka and OpenSearch are optional integrations and can remain disabled when not configured.

---

## 🏛️ Application Architecture

The project follows a modular structure separating application views, database operations, business logic, and integrations.

```text
BharatKart/
│
├── app.py
├── requirements.txt
├── README.md
├── .env.example
│
├── backend/
│   ├── database.py
│   ├── models.py
│   └── schemas.py
│
├── database/
│   ├── init_db.py
│   └── seed_data.py
│
├── frontend/
│   ├── components.py
│   ├── seller_portal.py
│   ├── store_views.py
│   └── checkout_and_ops.py
│
├── services/
│   ├── auth_service.py
│   ├── customer_service.py
│   ├── order_service.py
│   ├── product_service.py
│   ├── shop_service.py
│   ├── kafka_service.py
│   └── opensearch_service.py
│
├── utils/
│   ├── config.py
│   └── helpers.py
│
├── tests/
│
└── static/
```

*Note: This is a high-level architectural overview. Refer to the repository for the complete and current file structure.*

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or later.
- Git.
- PostgreSQL database access.
- A terminal such as PowerShell or Command Prompt.

### 1. Clone the Repository

```bash
git clone https://github.com/prachikaneriya23/BharatKart.git
```

### 2. Navigate to the Application Directory

```bash
cd BharatKart/BharatKart
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```cmd
venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create a `.env` file using the provided template:

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

Configure the required values in `.env`.

Example:

```env
# Primary Database
DATABASE_URL=your_postgresql_connection_uri

# Kafka - Optional
AIVEN_KAFKA_ENABLED=false

# OpenSearch - Optional
AIVEN_OPENSEARCH_ENABLED=false

# Optional AI Integration
GEMINI_API_KEY=

# Platform Configuration
FREE_SHIPPING_THRESHOLD=499.00
STANDARD_SHIPPING_FEE=49.00
LOW_STOCK_THRESHOLD=5

# Authentication
JWT_SECRET_KEY=generate_a_secure_random_secret
```

**Important:** Replace placeholders with your actual configuration values. Never upload `.env`, passwords, API keys, private keys, or certificates to GitHub.

### 7. Run BharatKart

```bash
python -m streamlit run app.py
```

Open the local application:

```text
http://localhost:8501
```

---

## 🔐 Security Considerations

- Environment variables are used for sensitive configuration.
- Authentication uses token-based security.
- Seller access is intended to be restricted to the seller's own shop and resources.
- Database operations use SQLAlchemy.
- Order and inventory workflows are designed to maintain consistency.
- Kafka event processing includes idempotency support.

Never commit real credentials, `.env` files, database backups, or private certificates.

---

## 🧪 Testing

Run the project's test suite using:

```bash
python -m pytest -v
```

---

## 🌱 Project Vision

Local retailers are an important part of India's economy, but many small businesses lack the digital infrastructure to reach customers online.

BharatKart aims to bridge this gap by bringing local stores together through a unified digital shopping experience.

**Our vision is simple: empower local businesses and make neighbourhood shopping accessible, convenient, and smarter.**

---

#
