from decimal import Decimal
import uuid
import pandas as pd
from pydantic import ValidationError
import streamlit as st
from backend.database import check_db_connection
from backend.schemas import CartItemInput, CheckoutRequest, CityDTO
from frontend.components import navigate_to
from services.kafka_service import relay_outbox_events
from services.opensearch_service import opensearch_manager
from services.order_service import (
    OrderProcessingError,
    calculate_totals,
    get_operations_metrics,
    get_order_by_id,
    place_order_atomic,
)
from services.product_service import refresh_cart_snapshot
from services.shop_service import approve_shop, list_registered_shops, reject_shop
from utils.config import settings
from utils.helpers import format_inr, get_offline_fallback_png, get_product_photo_url, get_service_health


def render_cart_and_checkout_page(city: CityDTO) -> None:
    st.title(f"Shopping Bag & Checkout — {city.label}")

    lines, warnings = refresh_cart_snapshot(city.id, st.session_state.cart)
    for w in warnings:
        st.warning(w)

    valid_pids = {line["product_id"]: line["quantity"] for line in lines}
    if valid_pids != st.session_state.cart:
        st.session_state.cart = valid_pids

    if not lines:
        st.markdown(
            f"""
            <div class="bk-panel" style="text-align: center; padding: 3rem 1.5rem;">
                <h3>Your BharatKart bag is empty</h3>
                <p style="color: #59524B; max-width: 460px; margin: 0.5rem auto 1.2rem auto;">
                    Explore physical partner stores in {city.name} to add items to your shopping bag.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns([2, 1.5, 2])
        with c2:
            if st.button("Browse Catalogue", type="primary", use_container_width=True):
                navigate_to("Catalogue")
        return

    if "checkout_idempotency_key" not in st.session_state or not st.session_state.checkout_idempotency_key:
        st.session_state.checkout_idempotency_key = f"idem-{uuid.uuid4().hex}"

    cart_col, summary_col = st.columns([1.45, 1.05], gap="large")

    with cart_col:
        st.subheader(f"Items in Your Multi-Store Bag ({city.name})")
        subtotal = sum(line["line_total"] for line in lines)

        # Group by physical shop
        items_by_shop: dict[str, list[dict]] = {}
        for line in lines:
            sname = line.get("shop_name", "Local Store")
            items_by_shop.setdefault(sname, []).append(line)

        for sname, shop_lines in items_by_shop.items():
            st.markdown(f"##### 🏬 Store: **{sname}**")
            for line in shop_lines:
                pid = line["product_id"]
                sku = line.get("sku", f"BK-{pid}")
                fresh_url = get_product_photo_url(sku) if sku in ("BK-HOM-005",) else line["image_url"]
                fallback_uri = get_offline_fallback_png(sku, line.get("category", "Product"))
                with st.container(border=True):
                    ic1, ic2, ic3 = st.columns([1, 2.3, 1.4], vertical_alignment="center")
                    with ic1:
                        st.markdown(
                            f"""
                            <img src="{fresh_url}"
                                 onerror="this.onerror=null; this.src='{fallback_uri}';"
                                 alt="{line['name']}"
                                 style="width:100%; height:86px; object-fit:cover; border-radius:8px; border:1px solid #DFD3C3;"/>
                            """,
                            unsafe_allow_html=True,
                        )
                    with ic2:
                        st.markdown(f"**{line['name']}**")
                        st.caption(f"{line['brand']} · Unit Price: {format_inr(line['unit_price'])}")
                        st.caption(f"Physical Stock: {line['stock_quantity']} units in {city.name}")
                    with ic3:
                        st.markdown(f"**{format_inr(line['line_total'])}**")
                        b_dec, b_qty, b_inc, b_rem = st.columns([1, 0.9, 1, 1.1])
                        with b_dec:
                            if st.button("−", key=f"dec_{pid}", type="secondary"):
                                if line["quantity"] <= 1:
                                    st.session_state.cart.pop(pid, None)
                                else:
                                    st.session_state.cart[pid] = line["quantity"] - 1
                                st.rerun()
                        with b_qty:
                            st.markdown(
                                f"<div style='text-align:center; padding-top:7px; font-weight:700;'>{line['quantity']}</div>",
                                unsafe_allow_html=True,
                            )
                        with b_inc:
                            can_inc = line["quantity"] < line["stock_quantity"]
                            if st.button("+", key=f"inc_{pid}", type="secondary", disabled=not can_inc):
                                st.session_state.cart[pid] = line["quantity"] + 1
                                st.rerun()
                        with b_rem:
                            if st.button("✕", key=f"rem_{pid}", type="secondary", help="Remove item"):
                                st.session_state.cart.pop(pid, None)
                                st.rerun()

    subtotal_val, shipping_val, total_val = calculate_totals(subtotal)
    threshold_dec = settings.FREE_SHIPPING_THRESHOLD
    remaining_for_free = max(0.0, float(threshold_dec) - float(subtotal_val))

    if shipping_val == 0:
        delivery_banner_html = (
            f'<div style="background-color:#E8F5E9; border:1px solid #A5D6A7; color:#1B5E20; '
            f'padding:0.55rem 0.75rem; border-radius:6px; font-size:0.82rem; font-weight:600; margin-top:0.65rem;">'
            f'🎉 You unlocked <strong>FREE Express Delivery</strong> (orders above {format_inr(threshold_dec)})!'
            f'</div>'
        )
    else:
        delivery_banner_html = (
            f'<div style="background-color:#FFF8E7; border:1px solid #E6C775; color:#6D4C00; '
            f'padding:0.55rem 0.75rem; border-radius:6px; font-size:0.82rem; font-weight:600; margin-top:0.65rem;">'
            f'🚚 Add <strong>{format_inr(remaining_for_free)}</strong> more for <strong>FREE Express Delivery</strong>.'
            f'</div>'
        )

    with summary_col:
        st.subheader("Order Summary")
        store_count = len(items_by_shop)
        st.markdown(
            f"""
            <div class="bk-panel">
                <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
                    <span>Fulfillment Stores</span>
                    <strong>{store_count} Store(s)</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
                    <span>Items Subtotal ({sum(l['quantity'] for l in lines)} units)</span>
                    <strong>{format_inr(subtotal_val)}</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
                    <span>Delivery ({city.name})</span>
                    <strong>{"FREE" if shipping_val == 0 else format_inr(shipping_val)}</strong>
                </div>
                <hr style="border-color:#DFD3C3; margin: 0.7rem 0;">
                <div style="display:flex; justify-content:space-between; font-size:1.15rem; color:#4A192C;">
                    <strong>Grand Total</strong>
                    <strong>{format_inr(total_val)}</strong>
                </div>
                {delivery_banner_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("Delivery Details")
        user = st.session_state.get("current_user")
        cust = st.session_state.get("registered_customer")

        with st.form("checkout_form"):
            customer_name = st.text_input("Full Name *", value=(user.full_name if user else (cust.full_name if cust else "")))
            customer_email = st.text_input("Email Address *", value=(user.email if user else (cust.email if cust else "")))
            customer_phone = st.text_input("Mobile Number *", value=(user.phone if user and user.phone else (cust.phone if cust else "")))
            shipping_address = st.text_area("Delivery Address *", value=(cust.default_address if cust else ""), height=75)
            pincode = st.text_input("Pincode *", max_chars=6, value=(cust.pincode if cust else ""))

            submitted = st.form_submit_button("Complete Checkout", type="primary", use_container_width=True)

        if submitted:
            try:
                req = CheckoutRequest(
                    idempotency_key=st.session_state.checkout_idempotency_key,
                    city_id=city.id,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    customer_phone=customer_phone,
                    shipping_address=shipping_address,
                    pincode=pincode,
                    items=[
                        CartItemInput(product_id=line["product_id"], quantity=line["quantity"])
                        for line in lines
                    ],
                )
                order_dto = place_order_atomic(req)
                st.session_state.cart = {}
                st.session_state.checkout_idempotency_key = f"idem-{uuid.uuid4().hex}"
                st.session_state.last_order_id = order_dto.order_id
                navigate_to("OrderConfirmation")

            except ValidationError as ve:
                for err in ve.errors():
                    field = err["loc"][-1] if err.get("loc") else "Field"
                    st.error(f"**{field}**: {err['msg']}")
            except OrderProcessingError as ope:
                st.error(str(ope))


def render_order_confirmation_page() -> None:
    order_id = st.session_state.last_order_id
    if not order_id:
        st.info("No recent order found in this session.")
        if st.button("Continue Shopping", type="primary"):
            navigate_to("Home")
        return

    order = get_order_by_id(order_id)
    if not order:
        st.error("Unable to load order confirmation details.")
        return

    st.markdown(
        f"""
        <div class="bk-hero" style="padding: 2rem 2.4rem;">
            <div class="bk-hero-eyebrow">Atomic Parent Order Committed · Status: {order.status}</div>
            <div class="bk-hero-title" style="font-size: 2rem;">Order Confirmed, {order.customer_name}!</div>
            <div class="bk-hero-desc">
                Parent Order <strong>{order.order_number}</strong> partitioned into <strong>{len(order.suborders)} shop-wise suborder(s)</strong>.
                Inventory updated atomically in PostgreSQL and outbox event <code>{order.outbox_event_id}</code> queued for Kafka streaming.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1.3, 1], gap="large")
    with c1:
        st.subheader("Shop-Wise Suborders & Tracking")
        for sub in order.suborders:
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong>🏬 {sub.shop_name} ({sub.shop_code})</strong>
                        <span class="bk-stock-ok">● {sub.status}</span>
                    </div>
                    <div style="font-size:0.85rem; color:#59524B; margin: 0.2rem 0;">
                        Suborder ID: <code>{sub.suborder_number}</code> · Subtotal: <strong>{format_inr(sub.subtotal)}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                items_df = [
                    {
                        "Product": it.product_name,
                        "Price": format_inr(it.unit_price),
                        "Qty": it.quantity,
                        "Total": format_inr(it.line_total),
                    }
                    for it in sub.items
                ]
                st.dataframe(pd.DataFrame(items_df), use_container_width=True, hide_index=True)

        st.markdown(
            f"""
            <div class="bk-panel">
                <div style="display:flex; justify-content:space-between; margin-bottom:0.35rem;">
                    <span>Subtotal</span><strong>{format_inr(order.subtotal_amount)}</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:0.35rem;">
                    <span>Shipping Fee</span><strong>{format_inr(order.shipping_fee)}</strong>
                </div>
                <hr style="border-color:#DFD3C3; margin: 0.6rem 0;">
                <div style="display:flex; justify-content:space-between; font-size:1.15rem; color:#4A192C;">
                    <strong>Total Amount Paid</strong><strong>{format_inr(order.total_amount)}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.subheader("Delivery Receipt")
        st.markdown(
            f"""
            <div class="bk-panel">
                <p><strong>Order Number:</strong> {order.order_number}</p>
                <p><strong>Order Date:</strong> {order.created_at.strftime('%d %b %Y, %I:%M %p UTC')}</p>
                <p><strong>Fulfillment City:</strong> {order.city_name}</p>
                <hr style="border-color:#DFD3C3; margin: 0.7rem 0;">
                <p><strong>Recipient:</strong> {order.customer_name}</p>
                <p><strong>Email:</strong> {order.customer_email}</p>
                <p><strong>Phone:</strong> +91 {order.customer_phone}</p>
                <p><strong>Delivery Address:</strong><br>{order.shipping_address} — {order.pincode}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    b1, b2, _ = st.columns([1.5, 1.5, 4])
    with b1:
        if st.button("Continue Shopping", type="primary", use_container_width=True):
            navigate_to("Home")
    with b2:
        if st.button("Operations Monitor", use_container_width=True):
            navigate_to("Operations")


def render_operations_dashboard() -> None:
    st.title("Operations & Aiven Architecture Monitor")
    st.caption("Live multi-city inventory telemetry, registered physical stores, transactional outbox queue, and service readiness.")

    metrics = get_operations_metrics()
    db_ok = check_db_connection()

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Products", metrics["total_products"])
    m2.metric("Partner Shops", metrics["total_shops"])
    m3.metric("Total Orders", metrics["total_orders"])
    m4.metric("Gross Revenue", format_inr(metrics["total_revenue"]))
    m5.metric("Network Stock", f"{metrics['total_inventory']} units")
    m6.metric("Outbox Events", metrics["pending_outbox"])

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)

    # Infrastructure Service Health
    st.subheader("Infrastructure & Aiven Service Health")
    health_items = get_service_health(db_ok=db_ok, pending_outbox=metrics["pending_outbox"])
    h_cols = st.columns(3)
    for idx, item in enumerate(health_items):
        badge_color = "#1B5E20" if item["active"] else "#B85D3B"
        with h_cols[idx]:
            st.markdown(
                f"""
                <div class="bk-panel">
                    <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:#59524B; font-weight:700;">
                        {item['service']}
                    </div>
                    <div style="font-family:'Playfair Display', serif; font-size:1.15rem; font-weight:700; color:#4A192C; margin:0.2rem 0;">
                        {item['engine']}
                    </div>
                    <div style="color:{badge_color}; font-weight:700; font-size:0.85rem; margin-bottom:0.4rem;">
                        ● {item['status']}
                    </div>
                    <div style="font-size:0.82rem; color:#22201E;">{item['note']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Integration Operations Actions (Outbox Relay & OpenSearch Sync)
    st.markdown("##### Service Operations & Synchronization")
    act1, act2, _ = st.columns([2, 2, 4])
    with act1:
        if st.button("⚡ Relay Pending Outbox to Kafka", type="primary", use_container_width=True):
            count = relay_outbox_events()
            st.success(f"Relayed {count} pending outbox event(s) to Kafka.")
            st.rerun()
    with act2:
        if st.button("🔍 Reindex All to OpenSearch", use_container_width=True):
            res = opensearch_manager.reindex_all_to_opensearch()
            st.info(f"OpenSearch Reindex: {res}")
            st.rerun()

    st.markdown("<hr style='border-color:#DFD3C3; margin: 1.2rem 0;'>", unsafe_allow_html=True)

    # Admin Shop Moderation
    st.subheader("Shop Approval & Moderation")
    all_shops = list_registered_shops()
    pending_shops = [s for s in all_shops if s.status == "PENDING"]
    if pending_shops:
        st.warning(f"**{len(pending_shops)} store(s) awaiting verification:**")
        for s in pending_shops:
            with st.expander(f"🏬 {s.shop_name} ({s.primary_category} · {s.city_name}) — Status: PENDING"):
                st.write(f"**Proprietor:** {s.owner_name} | **Email:** {s.owner_email} | **Phone:** {s.owner_phone}")
                st.write(f"**Address:** {s.shop_address} ({s.pincode}) | **PAN:** {s.pan_number} | **GSTIN:** {s.gstin}")
                a_col, r_col, _ = st.columns([1, 1, 3])
                with a_col:
                    if st.button("Approve Store", key=f"app_{s.id}", type="primary"):
                        approve_shop(s.id)
                        st.success(f"Approved {s.shop_name}!")
                        st.rerun()
                with r_col:
                    if st.button("Reject Store", key=f"rej_{s.id}"):
                        reject_shop(s.id)
                        st.error(f"Rejected {s.shop_name}.")
                        st.rerun()
    else:
        st.success("All partner physical stores are currently verified.")

    c_left, c_right = st.columns(2, gap="large")
    with c_left:
        st.subheader("City-Wise Inventory")
        st.dataframe(pd.DataFrame(metrics["city_inventory"]), use_container_width=True, hide_index=True)

    with c_right:
        st.subheader(f"Low-Stock Alerts (≤ {settings.LOW_STOCK_THRESHOLD} units)")
        if metrics["low_stock"]:
            st.dataframe(pd.DataFrame(metrics["low_stock"]), use_container_width=True, hide_index=True)
        else:
            st.success("All products across all cities have healthy stock levels.")

    st.subheader("Recent Orders")
    if metrics["recent_orders"]:
        st.dataframe(pd.DataFrame(metrics["recent_orders"]), use_container_width=True, hide_index=True)
    else:
        st.info("No orders placed yet.")

    st.subheader("Transactional Outbox Events (Aiven Kafka Relay Queue)")
    if metrics["outbox_events"]:
        st.dataframe(pd.DataFrame(metrics["outbox_events"]), use_container_width=True, hide_index=True)
    else:
        st.info("Outbox table is empty.")
