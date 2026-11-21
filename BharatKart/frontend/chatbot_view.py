from typing import Optional
import streamlit as st
from backend.schemas import CityDTO
from frontend.components import add_item_to_cart
from services.chatbot_service import assistant
from services.product_service import get_product_detail
from utils.helpers import format_inr


def render_floating_chatbot(city: CityDTO) -> None:
    """Render a compact floating shopping assistant at the bottom-right of every page.

    Default state: small floating icon. Clicking opens a compact panel. Closing restores icon.
    """
    if "chatbot_open" not in st.session_state:
        st.session_state.chatbot_open = False
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user = st.session_state.get("current_user")
    cust = st.session_state.get("registered_customer")
    customer_email = user.email if user else (cust.email if cust else None)

    # When collapsed, show small icon trigger
    if not st.session_state.chatbot_open:
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        _, right_col = st.columns([5, 1.2])
        with right_col:
            if st.button("💬 Shopping Assistant", key="open_floating_chatbot", type="primary", use_container_width=True):
                st.session_state.chatbot_open = True
                st.rerun()
        return

    # When open, render compact polished panel
    with st.container(border=True):
        h_left, h_right = st.columns([4, 1], vertical_alignment="center")
        with h_left:
            st.markdown(
                f"""
                <div style="font-weight:700; color:#4A192C; font-size:1.05rem;">
                    🛍️ BharatKart Shopping Intelligence
                </div>
                <div style="font-size:0.75rem; color:#59524B;">
                    Fulfillment Hub: <strong>{city.name}</strong> · Live Physical Store Stock
                </div>
                """,
                unsafe_allow_html=True,
            )
        with h_right:
            if st.button("✕ Close", key="close_floating_chatbot", type="secondary"):
                st.session_state.chatbot_open = False
                st.rerun()

        st.markdown("<hr style='margin: 0.5rem 0 0.8rem 0; border-color: #DFD3C3;'>", unsafe_allow_html=True)

        # Quick prompt buttons
        q1, q2, q3 = st.columns(3)
        with q1:
            if st.button("⚖️ Compare Sarees", key="float_chip_comp", use_container_width=True):
                _submit_floating_message("Compare sarees across handloom stores", city.id, customer_email)
        with q2:
            if st.button("🎯 Basket Optimizer", key="float_chip_opt", use_container_width=True):
                _submit_floating_message("I need Paithani silk stole, pure copper water bottle and leather wallet within ₹3,000", city.id, customer_email)
        with q3:
            if st.button("📦 My Orders", key="float_chip_orders", use_container_width=True):
                _submit_floating_message("Check my recent orders", city.id, customer_email)

        # Chat history container (scrollable compact height)
        chat_box = st.container(height=320)
        with chat_box:
            if not st.session_state.chat_history:
                st.caption("Ask me to find products in physical stores, compare prices, or optimize a multi-shop shopping list.")
            for idx, msg in enumerate(st.session_state.chat_history):
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.write(msg["content"])
                else:
                    with st.chat_message("assistant", avatar="🛍️"):
                        st.markdown(msg["content"])
                        if msg.get("basket_plan"):
                            plan = msg["basket_plan"]
                            items = plan.get("items", [])
                            st.info(f"Recommended Bundle: **{format_inr(plan.get('total_cost', 0))}** from **{plan.get('shop_count', 1)} store(s)**.")
                            if st.button("🛍️ Add Bundle to Bag", key=f"float_add_bundle_{idx}", type="primary"):
                                for it in items:
                                    p_dto = get_product_detail(it["product_id"], city.id)
                                    if p_dto and p_dto.stock_quantity > 0:
                                        add_item_to_cart(p_dto, 1)
                                st.success("Added bundle items to your shopping bag!")
                                st.rerun()

        # Input row
        with st.form("floating_chat_form", clear_on_submit=True):
            user_msg = st.text_input("Ask assistant...", placeholder="e.g. Find leather sandals under ₹1000", label_visibility="collapsed")
            _, f_sub, f_clear = st.columns([3.8, 1.2, 1.0])
            with f_sub:
                submit = st.form_submit_button("Send", type="primary", use_container_width=True)
            with f_clear:
                clear = st.form_submit_button("Reset", use_container_width=True)

        if submit and user_msg.strip():
            _submit_floating_message(user_msg.strip(), city.id, customer_email)
        if clear:
            st.session_state.chat_history = []
            st.rerun()


def _submit_floating_message(message: str, city_id: int, customer_email: Optional[str]) -> None:
    st.session_state.chat_history.append({"role": "user", "content": message})
    response = assistant.process_message(
        user_message=message,
        city_id=city_id,
        customer_email=customer_email,
        conversation_history=st.session_state.chat_history,
    )
    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": response.reply_text,
            "basket_plan": response.basket_plan,
            "suggested_products": response.suggested_products,
        }
    )
    st.rerun()


def render_chatbot_page(city: CityDTO) -> None:
    """Full-page standalone view when user clicks 'AI Assistant' in top navigation."""
    render_floating_chatbot(city)
