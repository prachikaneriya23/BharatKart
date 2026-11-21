import logging
import streamlit as st
from database.init_db import initialize_database
from frontend.chatbot_view import render_chatbot_page, render_floating_chatbot
from frontend.checkout_and_ops import (
    render_cart_and_checkout_page,
    render_operations_dashboard,
    render_order_confirmation_page,
)
from frontend.components import inject_custom_css, render_footer, render_header
from frontend.seller_portal import (
    render_auth_page,
    render_customer_registration_page,
    render_shop_registration_page,
)
from frontend.store_views import (
    render_catalogue_page,
    render_home_page,
    render_product_details_page,
    render_shop_storefront_page,
    render_shops_directory_page,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

st.set_page_config(
    page_title="BharatKart — Hyperlocal Multi-Store Physical Retail Marketplace",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource
def bootstrap_app() -> bool:
    initialize_database()
    return True


def main() -> None:
    bootstrap_app()
    inject_custom_css()
    current_city = render_header()

    current_user = st.session_state.get("current_user")
    if not current_user:
        # Require authentication before accessing shopping, cart, checkout, and store management
        render_auth_page(current_city)
        render_footer()
        return

    page = st.session_state.get("active_page", "Home")
    if page == "Home":
        render_home_page(current_city)
    elif page == "Catalogue":
        render_catalogue_page(current_city)
    elif page == "Shops":
        render_shops_directory_page(current_city)
    elif page == "ShopStorefront":
        render_shop_storefront_page(current_city)
    elif page == "ProductDetails":
        render_product_details_page(current_city)
    elif page == "Assistant":
        render_chatbot_page(current_city)
    elif page in ("RegisterShop", "SellerPortal"):
        render_shop_registration_page(current_city)
    elif page == "CustomerRegister":
        render_customer_registration_page(current_city)
    elif page == "Cart":
        render_cart_and_checkout_page(current_city)
    elif page == "OrderConfirmation":
        render_order_confirmation_page()
    elif page == "Operations":
        render_operations_dashboard()
    else:
        render_home_page(current_city)

    # Render floating chat widget at bottom-right of page (collapsible)
    if page != "Assistant":
        render_floating_chatbot(current_city)

    render_footer()


if __name__ == "__main__":
    main()
