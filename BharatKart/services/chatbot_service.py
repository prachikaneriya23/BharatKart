from dataclasses import dataclass, field
from decimal import Decimal
import itertools
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from rapidfuzz import fuzz, process
from sqlalchemy import or_, select
from backend.database import get_db_session
from backend.models import City, Customer, Inventory, Order, OrderItem, Product, Shop
from services.order_service import get_orders_for_customer
from utils.config import settings
from utils.helpers import format_inr

logger = logging.getLogger(__name__)


@dataclass
class ChatResponse:
    reply_text: str
    intent: str
    suggested_products: List[dict] = field(default_factory=list)
    comparison_items: List[dict] = field(default_factory=list)
    basket_plan: Optional[dict] = None
    orders_info: List[dict] = field(default_factory=list)


class ShoppingIntelligenceAssistant:
    """BharatKart Shopping Intelligence Assistant — Hyperlocal physical store discovery,

    cross-shop product comparison, smart multi-shop basket optimizer, and order assistance.
    """

    def __init__(self):
        self._gemini_client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai

                self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("Gemini API enabled for Shopping Intelligence Assistant.")
            except Exception as exc:
                logger.warning("Could not initialize Gemini Client: %s. Using rule-based engine.", exc)

    def process_message(
        self,
        user_message: str,
        city_id: int,
        customer_email: Optional[str] = None,
        conversation_history: Optional[List[dict]] = None,
    ) -> ChatResponse:
        """Route message to appropriate domain handler."""
        msg = user_message.strip()
        lower_msg = msg.lower()

        # 1. Order Status / Order Tracking Intent
        if any(w in lower_msg for w in ["order", "orders", "my order", "my orders", "recent orders", "track order", "order status", "where is my order"]):
            return self._handle_order_assistance(lower_msg, customer_email)

        # 2. Smart Multi-Shop Basket Optimizer Intent
        if any(k in lower_msg for k in ["basket", "shopping list", "bundle", "optimize", "within ₹", "under ₹"]) and (
            "," in msg or " and " in lower_msg or "need " in lower_msg
        ):
            return self._handle_basket_optimizer(msg, city_id)

        # 3. Cross-Shop Comparison Intent
        if any(k in lower_msg for k in ["compare", "difference between", "cheaper at", "versus", "vs"]):
            return self._handle_comparison(msg, city_id)

        # 4. Local Shop / Physical Store Search Intent
        if any(k in lower_msg for k in ["shop", "store", "roastery", "studio", "near me", "in my city"]):
            return self._handle_shop_discovery(msg, city_id)

        # 5. General Product Discovery & Recommendations under budget
        return self._handle_product_discovery(msg, city_id)

    def _extract_budget(self, text: str) -> Optional[float]:
        # Match explicit budget patterns: within ₹1,500, under 2000, max ₹800, etc.
        match = re.search(r"(?:under|within|below|budget of|upto|up to|max)\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]*)", text, re.I)
        if not match:
            match = re.search(r"(?:₹|rs\.?|inr)\s*(\d[\d,]*)", text, re.I)
        if match:
            clean_num = match.group(1).replace(",", "")
            if clean_num:
                return float(clean_num)
        return None

    def _handle_shop_discovery(self, query: str, city_id: int) -> ChatResponse:
        with get_db_session() as session:
            city = session.execute(select(City).where(City.id == city_id)).scalar_one_or_none()
            city_name = city.name if city else "your city"

            shops = session.execute(
                select(Shop).where(Shop.city_id == city_id, Shop.status == "VERIFIED")
            ).scalars().all()

            if not shops:
                return ChatResponse(
                    reply_text=f"Currently, there are no verified partner shops registered in **{city_name}**.",
                    intent="shop_discovery",
                )

            # Match category or keywords
            matched_shops = []
            for s in shops:
                ratio = fuzz.partial_ratio(query.lower(), f"{s.shop_name} {s.primary_category} {s.shop_description}".lower())
                if ratio >= 50 or any(w in query.lower() for w in s.primary_category.lower().split()):
                    matched_shops.append(s)

            if not matched_shops:
                matched_shops = list(shops)

            lines = [f"Found **{len(matched_shops)}** verified retail partner shop(s) in **{city_name}**:"]
            for s in matched_shops:
                lines.append(
                    f"• **{s.shop_name}** (`{s.shop_code}`) — *{s.primary_category}*\n"
                    f"  📍 {s.shop_address} ({s.pincode})\n"
                    f"  🚚 Daily courier pickup: {s.pickup_slot}\n"
                    f"  *{s.shop_description or 'Local physical merchant partner.'}*"
                )

            return ChatResponse(
                reply_text="\n\n".join(lines),
                intent="shop_discovery",
                suggested_products=[],
            )

    def _handle_comparison(self, query: str, city_id: int) -> ChatResponse:
        with get_db_session() as session:
            city = session.execute(select(City).where(City.id == city_id)).scalar_one()
            products = session.execute(
                select(Product, Inventory, Shop)
                .join(Inventory, Inventory.product_id == Product.id)
                .join(Shop, Shop.id == Product.shop_id)
                .where(Inventory.city_id == city_id)
            ).all()

            # Strip comparison boilerplate stopwords to isolate the target product concept
            boilerplate = r"\b(compare|comparing|comparison|versus|vs|between|difference|in|across|from|different|distinct|local|physical|shops?|stores?|products?|items?|merchants?|retailers?|cities|city)\b"
            cleaned_term = re.sub(boilerplate, " ", query, flags=re.I)
            cleaned_term = re.sub(r"\s+", " ", cleaned_term).strip().lower()

            # Handle common plurals (e.g. sarees -> saree, earbuds -> earbud)
            tokens = [w.rstrip("s") if len(w) > 4 and w.endswith("s") else w for w in cleaned_term.split()]

            scored = []
            for prod, inv, shop in products:
                prod_text = f"{prod.name} {prod.category} {prod.brand} {prod.description}".lower()
                prod_name_lower = prod.name.lower()

                if tokens:
                    # Strict semantic matching for requested items (e.g. 'saree')
                    token_matches = sum(1 for t in tokens if t in prod_text)
                    name_token_matches = sum(1 for t in tokens if t in prod_name_lower)
                    if token_matches == 0:
                        continue  # Exclude unrelated products (e.g. earbuds when searching for saree)

                    score = (name_token_matches * 60) + (token_matches * 30) + fuzz.partial_ratio(cleaned_term, prod_name_lower)
                else:
                    # Generic "compare stores": pick top rated featured items
                    score = float(prod.rating) * 20.0 + (10.0 if prod.is_featured else 0.0)

                scored.append((score, prod, inv, shop))

            # Prioritize distinct stores in comparison results
            scored.sort(key=lambda x: x[0], reverse=True)
            seen_shops = set()
            top_matches = []
            for item in scored:
                shop_id = item[3].id
                if shop_id not in seen_shops or len(top_matches) < 2:
                    seen_shops.add(shop_id)
                    top_matches.append(item)
                if len(top_matches) == 4:
                    break

            if not top_matches and scored:
                top_matches = scored[:4]

            item_label = cleaned_term.title() if cleaned_term else "Store"
            if not top_matches:
                return ChatResponse(
                    reply_text=f"I couldn't find matching **{item_label}** items in **{city.name}** across stores. Try searching for terms like 'saree', 'earbuds', 'copper', or 'sandals'.",
                    intent="comparison",
                )

            comparison_list = []
            lines = [f"### ⚖️ Cross-Shop {item_label} Comparison in {city.name}:"]
            for _, prod, inv, shop in top_matches:
                stock_status = f"✅ In Stock ({inv.stock_quantity} units)" if inv.stock_quantity > 0 else "❌ Out of Stock"
                lines.append(
                    f"**{prod.name}**\n"
                    f"- **Store:** {shop.shop_name} ({shop.shop_code})\n"
                    f"- **Price:** {format_inr(prod.price)} (MRP: {format_inr(prod.mrp)})\n"
                    f"- **Rating:** ★ {prod.rating} / 5.0\n"
                    f"- **Availability in {city.name}:** {stock_status}\n"
                    f"- **Key Attributes:** {prod.brand} · {prod.category}\n"
                    f"- **Craft & Specs:** {prod.description[:120]}..."
                )
                comparison_list.append(
                    {
                        "id": prod.id,
                        "name": prod.name,
                        "price": float(prod.price),
                        "mrp": float(prod.mrp),
                        "rating": float(prod.rating),
                        "shop_id": shop.id,
                        "shop_name": shop.shop_name,
                        "stock_quantity": inv.stock_quantity,
                    }
                )

            return ChatResponse(
                reply_text="\n\n".join(lines),
                intent="comparison",
                comparison_items=comparison_list,
            )

    def _handle_basket_optimizer(self, query: str, city_id: int) -> ChatResponse:
        """Smart Multi-Shop Basket Optimizer:

        Finds best product combination fulfilling a list across local stores within budget,
        supporting multi-store fulfillment with accurate semantic product matching.
        """
        budget = self._extract_budget(query)

        # Parse required items from list
        clean_text = re.sub(r"(?:i need|i want|shopping list|basket|within|under|below|for|budget of|₹|\d[\d,]*)", "", query, flags=re.I)
        raw_items = [part.strip() for part in re.split(r"[,;&]|\band\b", clean_text) if part.strip() and len(part.strip()) > 1]

        if not raw_items:
            raw_items = ["Paithani silk stole", "copper bottle", "leather wallet"]

        with get_db_session() as session:
            city = session.execute(select(City).where(City.id == city_id)).scalar_one()

            all_prods = session.execute(
                select(Product, Inventory, Shop)
                .join(Inventory, Inventory.product_id == Product.id)
                .join(Shop, Shop.id == Product.shop_id)
                .where(Inventory.city_id == city_id, Inventory.stock_quantity > 0)
            ).all()

            candidates_per_item: List[List[Tuple[Product, Inventory, Shop]]] = []
            unmatched_items = []

            for item_name in raw_items:
                item_lower = item_name.lower().strip()
                item_words = item_lower.split()

                scored_matches: List[Tuple[float, Tuple[Product, Inventory, Shop]]] = []
                for p, inv, s in all_prods:
                    target_text = f"{p.name} {p.category} {p.brand} {p.description}".lower()
                    name_score = fuzz.token_set_ratio(item_lower, p.name.lower())
                    desc_score = fuzz.token_set_ratio(item_lower, target_text)
                    score = (name_score * 0.7) + (desc_score * 0.3)

                    # Exact word containment in product name gives top priority
                    if all(w in p.name.lower() for w in item_words):
                        score = max(score, 98.0)
                    elif all(w in target_text for w in item_words):
                        score = max(score, 85.0)

                    if score >= 65.0:
                        scored_matches.append((score, (p, inv, s)))

                if scored_matches:
                    # Sort candidates by relevance score DESC, then lowest price ASC
                    scored_matches.sort(key=lambda x: (-x[0], x[1][0].price))
                    top_score = scored_matches[0][0]
                    # Keep close contenders within 10 points of top score, up to 3 candidates
                    candidates_per_item.append([match[1] for match in scored_matches if match[0] >= top_score - 10][:3])
                else:
                    unmatched_items.append(item_name)

            if not candidates_per_item:
                return ChatResponse(
                    reply_text=f"None of the items in your shopping list are currently available from partner shops in **{city.name}**.",
                    intent="basket_optimizer",
                )

            # Generate all Cartesian combinations of one product per item
            all_combos = list(itertools.product(*candidates_per_item))

            # Filter out combinations that pick the same product twice for different items (if multiple items requested)
            if len(candidates_per_item) > 1:
                valid_combos = [c for c in all_combos if len(set(p.id for p, inv, s in c)) == len(c)]
                if not valid_combos:
                    valid_combos = all_combos
            else:
                valid_combos = all_combos

            scored_plans = []
            for combo in valid_combos:
                total_cost = sum(Decimal(p.price) for p, inv, s in combo)
                unique_shops = set(s.id for p, inv, s in combo)
                shop_count = len(unique_shops)

                # Budget penalty if over budget
                if budget is not None and total_cost > Decimal(str(budget)):
                    budget_penalty = float(total_cost - Decimal(str(budget))) * 3.0
                else:
                    budget_penalty = 0.0

                # Multi-store synergy: minor per-shop overhead, priority on staying in budget
                score = float(total_cost) + (shop_count * 20.0) + budget_penalty
                scored_plans.append((score, total_cost, shop_count, combo))

            scored_plans.sort(key=lambda x: x[0])
            best_plan = scored_plans[0]
            _, best_total, best_shop_count, best_combo = best_plan

            # Structure recommendation
            bundle_products = []
            breakdown_lines = [
                f"### 🎯 Smart Multi-Shop Basket Recommendation ({city.name}):\n"
                f"• **Optimized Total:** {format_inr(best_total)}"
                f"{f' *(Within budget of {format_inr(budget)})*' if budget and best_total <= Decimal(str(budget)) else ''}\n"
                f"• **Fulfilled By:** {best_shop_count} local physical partner store(s) *(unified checkout)*"
            ]

            shop_grouping: Dict[str, List[str]] = {}
            for prod, inv, shop in best_combo:
                bundle_products.append(
                    {
                        "product_id": prod.id,
                        "name": prod.name,
                        "price": float(prod.price),
                        "shop_id": shop.id,
                        "shop_name": shop.shop_name,
                        "stock_quantity": inv.stock_quantity,
                    }
                )
                shop_grouping.setdefault(shop.shop_name, []).append(f"{prod.name} ({format_inr(prod.price)})")

            for s_name, item_strs in shop_grouping.items():
                breakdown_lines.append(f"**From Store: {s_name}:**\n" + "\n".join(f"  - {it}" for it in item_strs))

            if unmatched_items:
                breakdown_lines.append(f"⚠️ *Could not locate local in-stock options for: {', '.join(unmatched_items)}.*")

            breakdown_lines.append(
                "\n*You can add this entire multi-store bundle directly to your single combined shopping bag below.*"
            )

            plan_dict = {
                "total_cost": float(best_total),
                "shop_count": best_shop_count,
                "city_id": city.id,
                "city_name": city.name,
                "items": bundle_products,
            }

            return ChatResponse(
                reply_text="\n\n".join(breakdown_lines),
                intent="basket_optimizer",
                basket_plan=plan_dict,
                suggested_products=bundle_products,
            )

    def _handle_order_assistance(self, query: str, customer_email: Optional[str]) -> ChatResponse:
        if not customer_email:
            return ChatResponse(
                reply_text="To check your order details securely, please **Sign In** or register your profile under Buyer Membership first.",
                intent="order_assistance",
            )

        orders = get_orders_for_customer(customer_email)
        if not orders:
            return ChatResponse(
                reply_text=f"No placed orders were found under **{customer_email}** in BharatKart.",
                intent="order_assistance",
            )

        # Check for specific order number in query
        match = re.search(r"BK-[A-Z0-9]+", query, re.I)
        if match:
            target_num = match.group(0).upper()
            found = next((o for o in orders if o.order_number == target_num), None)
            if not found:
                return ChatResponse(
                    reply_text=f"Order **{target_num}** was not found in your account history.",
                    intent="order_assistance",
                )
            orders = [found]

        lines = [f"Found **{len(orders)}** verified order(s) for **{customer_email}**:"]
        orders_data = []
        for o in orders[:3]:
            item_summary = []
            for it in o.items:
                var_str = f" ({it.variant_info})" if it.variant_info else ""
                store_str = f" · *{it.shop_name}*" if it.shop_name else ""
                item_summary.append(f"  • {it.quantity} × **{it.product_name}**{var_str} — {format_inr(it.line_total)}{store_str}")

            sub_summary = []
            for sub in o.suborders:
                sub_summary.append(f"  • Store: **{sub.shop_name}** — Suborder `{sub.suborder_number}`: **{sub.status}**")

            lines.append(
                f"📦 **Order #{o.order_number}** (Total: {format_inr(o.total_amount)})\n"
                f"- **Overall Status:** {o.status}\n"
                f"- **Placed At:** {o.created_at.strftime('%d %b %Y, %I:%M %p UTC')}\n"
                f"- **Delivery To:** {o.shipping_address} ({o.city_name})\n"
                f"- **Products in this Order:**\n" + ("\n".join(item_summary) if item_summary else "  • Items processed") + "\n"
                f"- **Shop-wise Fulfillment:**\n" + ("\n".join(sub_summary) if sub_summary else "  • Processing dispatch")
            )
            orders_data.append({"order_number": o.order_number, "status": o.status, "total": float(o.total_amount)})

        return ChatResponse(
            reply_text="\n\n".join(lines),
            intent="order_assistance",
            orders_info=orders_data,
        )

    def _handle_product_discovery(self, query: str, city_id: int) -> ChatResponse:
        budget = self._extract_budget(query)
        with get_db_session() as session:
            city = session.execute(select(City).where(City.id == city_id)).scalar_one()

            stmt = (
                select(Product, Inventory, Shop)
                .join(Inventory, Inventory.product_id == Product.id)
                .join(Shop, Shop.id == Product.shop_id)
                .where(Inventory.city_id == city_id, Inventory.stock_quantity > 0)
            )
            if budget is not None:
                stmt = stmt.where(Product.price <= Decimal(str(budget)))

            products = session.execute(stmt).all()
            if not products:
                return ChatResponse(
                    reply_text=f"No products found matching your criteria in **{city.name}**{f' under {format_inr(budget)}' if budget else ''}.",
                    intent="product_discovery",
                )

            scored = []
            for prod, inv, shop in products:
                score = fuzz.partial_ratio(query.lower(), f"{prod.name} {prod.category} {prod.brand} {prod.description}".lower())
                scored.append((score, prod, inv, shop))

            scored.sort(key=lambda x: (x[0], x[1].rating), reverse=True)
            top_products = [x for x in scored if x[0] >= 35][:5]
            if not top_products:
                top_products = scored[:4]

            lines = [f"Found these verified in-stock items in **{city.name}**:"]
            suggested = []
            for _, prod, inv, shop in top_products:
                lines.append(
                    f"• **{prod.name}** — **{format_inr(prod.price)}** (★ {prod.rating})\n"
                    f"  Store: *{shop.shop_name}* · In Stock: {inv.stock_quantity} units ready in {city.name}\n"
                    f"  {prod.description[:110]}..."
                )
                suggested.append(
                    {
                        "product_id": prod.id,
                        "name": prod.name,
                        "price": float(prod.price),
                        "shop_id": shop.id,
                        "shop_name": shop.shop_name,
                        "stock_quantity": inv.stock_quantity,
                    }
                )

            return ChatResponse(
                reply_text="\n\n".join(lines),
                intent="product_discovery",
                suggested_products=suggested,
            )


assistant = ShoppingIntelligenceAssistant()
