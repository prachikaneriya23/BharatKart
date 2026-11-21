from pathlib import Path
from typing import Optional
import streamlit as st
from backend.schemas import CityDTO, ProductCardDTO
from services.product_service import get_active_cities
from utils.config import settings
from utils.helpers import format_inr, get_offline_fallback_png, get_product_photo_url


def inject_custom_css() -> None:
    css_path = Path(__file__).parent / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def init_session_state(cities: list[CityDTO]) -> None:
    if "selected_city_id" not in st.session_state:
        st.session_state.selected_city_id = cities[0].id
    if "cart" not in st.session_state:
        st.session_state.cart = {}
    if "active_page" not in st.session_state:
        st.session_state.active_page = "Home"
    if "selected_product_id" not in st.session_state:
        st.session_state.selected_product_id = None
    if "selected_shop_id" not in st.session_state:
        st.session_state.selected_shop_id = None
    if "pending_city_id" not in st.session_state:
        st.session_state.pending_city_id = None
    if "global_search" not in st.session_state:
        st.session_state.global_search = ""
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = "All"
    if "last_order_id" not in st.session_state:
        st.session_state.last_order_id = None
    if "last_registered_shop" not in st.session_state:
        st.session_state.last_registered_shop = None
    if "registered_customer" not in st.session_state:
        st.session_state.registered_customer = None
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def navigate_to(
    page: str,
    product_id: Optional[int] = None,
    shop_id: Optional[int] = None,
    category: Optional[str] = None,
) -> None:
    st.session_state.active_page = page
    if product_id is not None:
        st.session_state.selected_product_id = product_id
    if shop_id is not None:
        st.session_state.selected_shop_id = shop_id
    if category is not None:
        st.session_state.selected_category = category
    st.rerun()


def add_item_to_cart(product: ProductCardDTO, qty: int = 1) -> None:
    current_qty = st.session_state.cart.get(product.id, 0)
    new_qty = current_qty + qty
    if product.stock_quantity <= 0:
        st.toast(f"'{product.name}' is currently out of stock in {product.city_name}.", icon="⚠️")
        return
    if new_qty > product.stock_quantity:
        st.session_state.cart[product.id] = product.stock_quantity
        st.toast(f"Maximum available stock ({product.stock_quantity}) reached for '{product.name}'.", icon="ℹ️")
    else:
        st.session_state.cart[product.id] = new_qty
        st.toast(f"Added {qty} × {product.name} to your bag.", icon="🛍️")


def render_header() -> CityDTO:
    cities = get_active_cities()
    init_session_state(cities)
    city_by_id = {c.id: c for c in cities}
    current_city = city_by_id.get(st.session_state.selected_city_id, cities[0])

    total_cart_units = sum(st.session_state.cart.values())
    user = st.session_state.get("current_user")
    cust = st.session_state.get("registered_customer")

    if user:
        welcome_tag = f"Logged in as **{user.full_name}** ({user.role.upper()})"
    elif cust:
        welcome_tag = f"Welcome back, **{cust.full_name.split()[0]}**"
    else:
        welcome_tag = "Hyperlocal Physical Marketplace · Please Sign In to Access Stores"

    st.markdown(
        f"""
        <div class="bk-topbar">
            <span>{welcome_tag}</span>
            <span>Fulfillment City: <strong>{current_city.label}</strong></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_brand, col_city, col_nav = st.columns([1.6, 2.0, 6.4], vertical_alignment="center")

    with col_brand:
        st.markdown(
            """
            <div class="bk-brand-mark" style="cursor: pointer;" onclick="window.location.reload();">BharatKart</div>
            <div class="bk-brand-sub">Hyperlocal Multi-Store Marketplace</div>
            """,
            unsafe_allow_html=True,
        )

    with col_city:
        city_options = [c.id for c in cities]
        current_idx = city_options.index(current_city.id)
        chosen_city_id = st.selectbox(
            "Delivering to",
            options=city_options,
            index=current_idx,
            format_func=lambda cid: f"📍 {city_by_id[cid].label}",
            key="header_city_selector",
        )
        if chosen_city_id != current_city.id:
            if st.session_state.cart:
                st.session_state.pending_city_id = chosen_city_id
            else:
                st.session_state.selected_city_id = chosen_city_id
                st.session_state.pending_city_id = None
                st.rerun()

    with col_nav:
        if not user:
            # Unauthenticated state
            _, c_auth = st.columns([4, 2])
            with c_auth:
                if st.button("🔐 Sign In / Register", use_container_width=True, type="primary"):
                    navigate_to("CustomerRegister")
        else:
            # Authenticated state
            n1, n2, n3, n4, n5, n6, n7, n8 = st.columns([0.8, 1.0, 0.95, 1.25, 1.15, 0.95, 0.95, 0.95])
            with n1:
                if st.button("Home", use_container_width=True, type="primary" if st.session_state.active_page == "Home" else "secondary"):
                    navigate_to("Home")
            with n2:
                if st.button("Catalogue", use_container_width=True, type="primary" if st.session_state.active_page == "Catalogue" else "secondary"):
                    navigate_to("Catalogue")
            with n3:
                if st.button("Shops", use_container_width=True, type="primary" if st.session_state.active_page == "Shops" else "secondary"):
                    navigate_to("Shops")
            with n4:
                if st.button("AI Assistant", use_container_width=True, type="primary" if st.session_state.active_page == "Assistant" else "secondary"):
                    navigate_to("Assistant")
            with n5:
                if user.role == "seller":
                    if st.button("My Store", use_container_width=True, type="primary" if st.session_state.active_page == "SellerPortal" else "secondary"):
                        navigate_to("SellerPortal")
                elif user.role == "admin":
                    if st.button("Operations", use_container_width=True, type="primary" if st.session_state.active_page == "Operations" else "secondary"):
                        navigate_to("Operations")
                else:
                    if st.button("My Orders", use_container_width=True, type="primary" if st.session_state.active_page == "CustomerRegister" else "secondary"):
                        navigate_to("CustomerRegister")
            with n6:
                cart_label = f"Bag ({total_cart_units})" if total_cart_units > 0 else "Bag"
                if st.button(cart_label, use_container_width=True, type="primary" if st.session_state.active_page == "Cart" else "secondary"):
                    navigate_to("Cart")
            with n7:
                acc_label = f"👤 {user.full_name.split()[0]}"
                if st.button(acc_label, use_container_width=True, type="primary" if st.session_state.active_page == "CustomerRegister" else "secondary"):
                    navigate_to("CustomerRegister")
            with n8:
                if st.button("Log Out", key="nav_logout_btn", use_container_width=True, type="secondary"):
                    st.session_state.current_user = None
                    st.session_state.registered_customer = None
                    st.session_state.cart = {}
                    st.session_state.checkout_idempotency_key = None
                    st.session_state.active_page = "Home"
                    st.rerun()

    if st.session_state.pending_city_id is not None:
        target_city = city_by_id[st.session_state.pending_city_id]
        st.warning(
            f"**Switch fulfillment city to {target_city.label}?** "
            f"Your shopping bag holds items reserved in **{current_city.label}**. Changing cities will clear your bag."
        )
        c_yes, c_no, _ = st.columns([1.6, 1.6, 4.8])
        with c_yes:
            if st.button("Confirm & Clear Bag", type="primary", key="confirm_city_switch"):
                st.session_state.cart = {}
                st.session_state.selected_city_id = target_city.id
                st.session_state.pending_city_id = None
                st.rerun()
        with c_no:
            if st.button("Keep Current City", type="secondary", key="cancel_city_switch"):
                st.session_state.pending_city_id = None
                st.rerun()

    st.markdown("<hr style='margin: 0.6rem 0 1.2rem 0; border-color: #DFD3C3;'>", unsafe_allow_html=True)
    return city_by_id[st.session_state.selected_city_id]


def render_product_card(product: ProductCardDTO, key_prefix: str) -> None:
    if product.stock_quantity <= 0:
        stock_html = '<div class="bk-stock-out">Out of Stock in this city</div>'
    elif product.stock_quantity <= settings.LOW_STOCK_THRESHOLD:
        stock_html = f'<div class="bk-stock-low">Only {product.stock_quantity} left in stock</div>'
    else:
        stock_html = f'<div class="bk-stock-ok">In Stock ({product.stock_quantity} available)</div>'

    discount_badge = (
        f'<span class="bk-discount">{product.discount_percent}% OFF</span>'
        if product.discount_percent > 0
        else ""
    )

    fallback_uri = get_offline_fallback_png(product.sku, product.category)
    shop_badge = f'<div style="font-size:0.75rem; color:#8C3A27; font-weight:600; margin-top:2px;">🏬 {product.shop_name or "Local Partner"}</div>'

    st.markdown(
        f"""
        <div class="bk-card">
            <div class="bk-card-img-wrap">
                <img src="{get_product_photo_url(product.sku) if product.sku == 'BK-HOM-005' else product.image_url}"
                     onerror="this.onerror=null; this.src='{fallback_uri}';"
                     alt="{product.name}"
                     class="bk-card-img"
                     loading="lazy"/>
            </div>
            <div class="bk-card-brand">{product.brand} · ★ {product.rating}</div>
            <div class="bk-card-title">{product.name}</div>
            {shop_badge}
            <div class="bk-price-row">
                <span class="bk-price">{format_inr(product.price)}</span>
                <span class="bk-mrp">{format_inr(product.mrp)}</span>
                {discount_badge}
            </div>
            {stock_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Details", key=f"{key_prefix}_view_{product.id}", use_container_width=True):
            navigate_to("ProductDetails", product_id=product.id)
    with b2:
        disabled = product.stock_quantity <= 0
        if st.button(
            "Add to Bag" if not disabled else "Sold Out",
            key=f"{key_prefix}_add_{product.id}",
            type="primary" if not disabled else "secondary",
            disabled=disabled,
            use_container_width=True,
        ):
            add_item_to_cart(product, 1)
            st.rerun()


def render_footer() -> None:
    st.markdown(
        """
        <div class="bk-footer">
            <div><strong>BharatKart</strong> · Curated Hyperlocal Multi-Store Physical Retail Marketplace</div>
            <div>Powered by Aiven PostgreSQL, Apache Kafka Outbox & OpenSearch Engine</div>
            <div>Bengaluru · Mumbai · Pune · Mangalore</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
