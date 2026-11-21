from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from sqlalchemy import or_, select
from backend.database import get_db_session
from backend.models import City, Inventory, Product, ProductVariant, Shop
from utils.config import settings

logger = logging.getLogger(__name__)

PRODUCT_INDEX = "bharatkart_products"
SHOP_INDEX = "bharatkart_shops"


class OpenSearchManager:
    """Aiven OpenSearch discovery engine with full-text search, fuzzy matching, and PostgreSQL fallback."""

    def __init__(self):
        self._client = None
        self._init_error = None
        self._init_client()

    def _init_client(self):
        host_url = settings.OPENSEARCH_HOST or settings.OPENSEARCH_URL
        if not host_url:
            self._init_error = "Missing OPENSEARCH_HOST or OPENSEARCH_URL environment variable"
            logger.info("OpenSearch host not configured. Running in PostgreSQL search fallback mode.")
            return

        try:
            from opensearchpy import OpenSearch

            parsed = urlparse(host_url)
            host = parsed.hostname or host_url
            port = parsed.port or (443 if (parsed.scheme == "https" or settings.OPENSEARCH_USE_SSL) else 9200)
            use_ssl = parsed.scheme == "https" or settings.OPENSEARCH_USE_SSL

            auth = None
            if settings.OPENSEARCH_USERNAME and settings.OPENSEARCH_PASSWORD:
                auth = (settings.OPENSEARCH_USERNAME, settings.OPENSEARCH_PASSWORD)
            elif parsed.username and parsed.password:
                auth = (parsed.username, parsed.password)

            self._client = OpenSearch(
                hosts=[{"host": host, "port": port}],
                http_auth=auth,
                use_ssl=use_ssl,
                verify_certs=settings.OPENSEARCH_VERIFY_CERTS,
                ssl_show_warn=False,
                timeout=5,
            )
            # Test actual connection
            if self._client.ping():
                self._init_error = None
                logger.info("Connected to OpenSearch cluster at %s:%s", host, port)
                self.create_indices()
            else:
                self._init_error = f"Ping failed for OpenSearch cluster at {host}:{port}"
                logger.warning("OpenSearch ping returned false. Falling back to PostgreSQL search.")
                self._client = None
        except Exception as exc:
            self._init_error = str(exc)
            logger.warning("Could not connect to OpenSearch cluster: %s. Using PostgreSQL fallback.", exc)
            self._client = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    @property
    def missing_credentials(self) -> List[str]:
        missing = []
        if not (settings.OPENSEARCH_HOST or settings.OPENSEARCH_URL):
            missing.append("OPENSEARCH_HOST")
        if not settings.OPENSEARCH_USERNAME:
            missing.append("OPENSEARCH_USERNAME")
        if not settings.OPENSEARCH_PASSWORD:
            missing.append("OPENSEARCH_PASSWORD")
        return missing

    def create_indices(self) -> bool:
        if not self._client:
            return False
        try:
            product_mapping = {
                "settings": {"number_of_shards": 1, "number_of_replicas": 1},
                "mappings": {
                    "properties": {
                        "id": {"type": "integer"},
                        "sku": {"type": "keyword"},
                        "name": {"type": "text", "analyzer": "standard"},
                        "brand": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "category": {"type": "keyword"},
                        "description": {"type": "text"},
                        "price": {"type": "float"},
                        "mrp": {"type": "float"},
                        "rating": {"type": "float"},
                        "shop_id": {"type": "integer"},
                        "shop_name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "city_id": {"type": "integer"},
                        "city_name": {"type": "keyword"},
                        "stock_quantity": {"type": "integer"},
                        "variants": {"type": "keyword"},
                    }
                },
            }

            shop_mapping = {
                "settings": {"number_of_shards": 1, "number_of_replicas": 1},
                "mappings": {
                    "properties": {
                        "id": {"type": "integer"},
                        "shop_code": {"type": "keyword"},
                        "shop_name": {"type": "text", "analyzer": "standard"},
                        "owner_name": {"type": "text"},
                        "primary_category": {"type": "keyword"},
                        "city_id": {"type": "integer"},
                        "city_name": {"type": "keyword"},
                        "shop_address": {"type": "text"},
                        "status": {"type": "keyword"},
                    }
                },
            }

            if not self._client.indices.exists(index=PRODUCT_INDEX):
                self._client.indices.create(index=PRODUCT_INDEX, body=product_mapping)
            if not self._client.indices.exists(index=SHOP_INDEX):
                self._client.indices.create(index=SHOP_INDEX, body=shop_mapping)
            return True
        except Exception as exc:
            logger.error("Error creating OpenSearch indices: %s", exc)
            return False

    def index_product(self, doc: dict) -> bool:
        if not self._client:
            return False
        try:
            doc_id = f"{doc['id']}-{doc.get('city_id', 1)}"
            self._client.index(index=PRODUCT_INDEX, id=doc_id, body=doc, refresh=True)
            return True
        except Exception as exc:
            logger.error("Error indexing product in OpenSearch: %s", exc)
            return False

    def index_shop(self, doc: dict) -> bool:
        if not self._client:
            return False
        try:
            self._client.index(index=SHOP_INDEX, id=str(doc["id"]), body=doc, refresh=True)
            return True
        except Exception as exc:
            logger.error("Error indexing shop in OpenSearch: %s", exc)
            return False

    def handle_kafka_event(self, event_type: str, payload: dict) -> None:
        """Update OpenSearch index in response to consumed Kafka event."""
        if not self._client:
            return

        try:
            if event_type in ("product.updated", "product.created"):
                pid = payload.get("product_id")
                if pid:
                    with get_db_session() as session:
                        prod = session.execute(
                            select(Product, Inventory, City, Shop)
                            .join(Inventory, Inventory.product_id == Product.id)
                            .join(City, City.id == Inventory.city_id)
                            .outerjoin(Shop, Shop.id == Product.shop_id)
                            .where(Product.id == pid)
                        ).first()
                        if prod:
                            p, inv, c, s = prod
                            self.index_product(
                                {
                                    "id": p.id,
                                    "sku": p.sku,
                                    "name": p.name,
                                    "brand": p.brand,
                                    "category": p.category,
                                    "description": p.description,
                                    "price": float(p.price),
                                    "mrp": float(p.mrp),
                                    "rating": float(p.rating),
                                    "shop_id": s.id if s else p.shop_id,
                                    "shop_name": s.shop_name if s else "Local Store",
                                    "city_id": c.id,
                                    "city_name": f"{c.name}, {c.state}",
                                    "stock_quantity": inv.stock_quantity,
                                }
                            )

            elif event_type in ("shop.updated", "shop.approved"):
                sid = payload.get("shop_id")
                if sid:
                    with get_db_session() as session:
                        shop_row = session.execute(
                            select(Shop, City).join(City, City.id == Shop.city_id).where(Shop.id == sid)
                        ).first()
                        if shop_row:
                            s, c = shop_row
                            self.index_shop(
                                {
                                    "id": s.id,
                                    "shop_code": s.shop_code,
                                    "shop_name": s.shop_name,
                                    "owner_name": s.owner_name,
                                    "primary_category": s.primary_category,
                                    "city_id": c.id,
                                    "city_name": f"{c.name}, {c.state}",
                                    "shop_address": s.shop_address,
                                    "status": s.status,
                                }
                            )
        except Exception as exc:
            logger.error("Error syncing Kafka event to OpenSearch: %s", exc)

    def search_products(
        self,
        query: str = "",
        city_id: Optional[int] = None,
        shop_id: Optional[int] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: Optional[str] = None,
    ) -> List[dict]:
        """Search products via OpenSearch if connected, or fallback to PostgreSQL."""
        if self._client:
            try:
                must_clauses: List[dict] = []
                filter_clauses: List[dict] = []

                if query and query.strip():
                    must_clauses.append(
                        {
                            "multi_match": {
                                "query": query.strip(),
                                "fields": ["name^3", "brand^2", "category", "description", "shop_name"],
                                "fuzziness": "AUTO",
                            }
                        }
                    )
                else:
                    must_clauses.append({"match_all": {}})

                if city_id is not None:
                    filter_clauses.append({"term": {"city_id": city_id}})
                if shop_id is not None:
                    filter_clauses.append({"term": {"shop_id": shop_id}})
                if category and category != "All":
                    filter_clauses.append({"term": {"category": category}})
                if min_price is not None or max_price is not None:
                    price_range = {}
                    if min_price is not None:
                        price_range["gte"] = min_price
                    if max_price is not None:
                        price_range["lte"] = max_price
                    filter_clauses.append({"range": {"price": price_range}})

                sort_clause: List[Any] = []
                if sort_by == "Price: Low to High":
                    sort_clause.append({"price": {"order": "asc"}})
                elif sort_by == "Price: High to Low":
                    sort_clause.append({"price": {"order": "desc"}})
                elif sort_by == "Top Rated":
                    sort_clause.append({"rating": {"order": "desc"}})

                search_body = {
                    "query": {"bool": {"must": must_clauses, "filter": filter_clauses}},
                    "size": 50,
                }
                if sort_clause:
                    search_body["sort"] = sort_clause

                response = self._client.search(index=PRODUCT_INDEX, body=search_body)
                hits = response.get("hits", {}).get("hits", [])
                return [h["_source"] for h in hits]
            except Exception as exc:
                logger.warning("OpenSearch query failed: %s. Using PostgreSQL fallback.", exc)

        # Authoritative PostgreSQL Search Fallback
        return self._search_products_postgresql(
            query=query,
            city_id=city_id,
            shop_id=shop_id,
            category=category,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
        )

    def _search_products_postgresql(
        self,
        query: str,
        city_id: Optional[int],
        shop_id: Optional[int],
        category: Optional[str],
        min_price: Optional[float],
        max_price: Optional[float],
        sort_by: Optional[str] = None,
    ) -> List[dict]:
        with get_db_session() as session:
            stmt = (
                select(Product, Inventory, City, Shop)
                .join(Inventory, Inventory.product_id == Product.id)
                .join(City, City.id == Inventory.city_id)
                .outerjoin(Shop, Shop.id == Product.shop_id)
            )
            if city_id is not None:
                stmt = stmt.where(City.id == city_id)
            if shop_id is not None:
                stmt = stmt.where(Product.shop_id == shop_id)
            if category and category != "All":
                stmt = stmt.where(Product.category == category)
            if min_price is not None:
                stmt = stmt.where(Product.price >= Decimal(str(min_price)))
            if max_price is not None:
                stmt = stmt.where(Product.price <= Decimal(str(max_price)))

            if query and query.strip():
                term = f"%{query.strip()}%"
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
                stmt = stmt.order_by(Product.price.asc())
            elif sort_by == "Price: High to Low":
                stmt = stmt.order_by(Product.price.desc())
            elif sort_by == "Top Rated":
                stmt = stmt.order_by(Product.rating.desc())

            rows = session.execute(stmt.limit(50)).all()
            results = []
            for prod, inv, city, shop in rows:
                results.append(
                    {
                        "id": prod.id,
                        "sku": prod.sku,
                        "name": prod.name,
                        "brand": prod.brand,
                        "category": prod.category,
                        "description": prod.description,
                        "price": float(prod.price),
                        "mrp": float(prod.mrp),
                        "rating": float(prod.rating),
                        "shop_id": shop.id if shop else prod.shop_id,
                        "shop_name": shop.shop_name if shop else "Local Store",
                        "city_id": city.id,
                        "city_name": f"{city.name}, {city.state}",
                        "stock_quantity": inv.stock_quantity,
                    }
                )
            return results

    def search_shops(
        self, query: str = "", city_id: Optional[int] = None, category: Optional[str] = None
    ) -> List[dict]:
        """Discover verified physical partner shops via OpenSearch or PostgreSQL fallback."""
        if self._client:
            try:
                must = []
                filters = [{"term": {"status": "VERIFIED"}}]
                if query and query.strip():
                    must.append(
                        {
                            "multi_match": {
                                "query": query.strip(),
                                "fields": ["shop_name^3", "primary_category^2", "owner_name", "shop_address"],
                                "fuzziness": "AUTO",
                            }
                        }
                    )
                else:
                    must.append({"match_all": {}})
                if city_id is not None:
                    filters.append({"term": {"city_id": city_id}})
                if category and category != "All":
                    filters.append({"term": {"primary_category": category}})

                body = {"query": {"bool": {"must": must, "filter": filters}}, "size": 30}
                res = self._client.search(index=SHOP_INDEX, body=body)
                return [h["_source"] for h in res.get("hits", {}).get("hits", [])]
            except Exception as exc:
                logger.warning("OpenSearch shop search failed: %s. Using PostgreSQL fallback.", exc)

        with get_db_session() as session:
            stmt = select(Shop, City).join(City, City.id == Shop.city_id).where(Shop.status == "VERIFIED")
            if city_id is not None:
                stmt = stmt.where(Shop.city_id == city_id)
            if category and category != "All":
                stmt = stmt.where(Shop.primary_category == category)
            if query and query.strip():
                term = f"%{query.strip()}%"
                stmt = stmt.where(
                    or_(
                        Shop.shop_name.ilike(term),
                        Shop.primary_category.ilike(term),
                        Shop.owner_name.ilike(term),
                        Shop.shop_address.ilike(term),
                    )
                )
            rows = session.execute(stmt.limit(30)).all()
            return [
                {
                    "id": s.id,
                    "shop_code": s.shop_code,
                    "shop_name": s.shop_name,
                    "owner_name": s.owner_name,
                    "primary_category": s.primary_category,
                    "city_id": c.id,
                    "city_name": f"{c.name}, {c.state}",
                    "shop_address": s.shop_address,
                    "status": s.status,
                }
                for s, c in rows
            ]

    def reindex_all_to_opensearch(self) -> dict:
        """Full reindex of all PostgreSQL products and shops into OpenSearch."""
        if not self._client:
            return {"status": "skipped", "message": "OpenSearch not connected. Configured missing: " + ", ".join(self.missing_credentials)}

        self.create_indices()
        product_count = 0
        shop_count = 0

        with get_db_session() as session:
            shops = session.execute(select(Shop, City).join(City, City.id == Shop.city_id)).all()
            for s, c in shops:
                self.index_shop(
                    {
                        "id": s.id,
                        "shop_code": s.shop_code,
                        "shop_name": s.shop_name,
                        "owner_name": s.owner_name,
                        "primary_category": s.primary_category,
                        "city_id": c.id,
                        "city_name": f"{c.name}, {c.state}",
                        "shop_address": s.shop_address,
                        "status": s.status,
                    }
                )
                shop_count += 1

            prod_rows = session.execute(
                select(Product, Inventory, City, Shop)
                .join(Inventory, Inventory.product_id == Product.id)
                .join(City, City.id == Inventory.city_id)
                .outerjoin(Shop, Shop.id == Product.shop_id)
            ).all()

            for prod, inv, city, shop in prod_rows:
                variants = session.execute(
                    select(ProductVariant.variant_value).where(ProductVariant.product_id == prod.id)
                ).scalars().all()

                self.index_product(
                    {
                        "id": prod.id,
                        "sku": prod.sku,
                        "name": prod.name,
                        "brand": prod.brand,
                        "category": prod.category,
                        "description": prod.description,
                        "price": float(prod.price),
                        "mrp": float(prod.mrp),
                        "rating": float(prod.rating),
                        "shop_id": shop.id if shop else prod.shop_id,
                        "shop_name": shop.shop_name if shop else "Local Store",
                        "city_id": city.id,
                        "city_name": f"{city.name}, {city.state}",
                        "stock_quantity": inv.stock_quantity,
                        "variants": list(variants),
                    }
                )
                product_count += 1

        return {
            "status": "success",
            "indexed_products": product_count,
            "indexed_shops": shop_count,
        }


opensearch_manager = OpenSearchManager()
