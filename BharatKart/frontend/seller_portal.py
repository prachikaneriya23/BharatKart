import pandas as pd
from pydantic import ValidationError
import streamlit as st
from backend.schemas import (
    CityDTO,
    CustomerRegistrationRequest,
    ProductCreateRequest,
    ProductUpdateRequest,
    ShopRegistrationRequest,
    UserLoginRequest,
)
from frontend.components import navigate_to
from services.auth_service import authenticate_user
from services.customer_service import (
    CustomerRegistrationError,
    get_customer_by_email,
    register_or_update_customer,
)
from services.order_service import get_orders_for_customer, get_suborders_for_shop, update_suborder_status
from services.product_service import (
    create_product,
    delete_product,
    get_active_cities,
    get_categories,
    list_products_for_city,
    update_inventory_stock,
    update_product,
)
from services.shop_service import (
    ShopRegistrationError,
    get_shop_by_id,
    list_registered_shops,
    register_shop_atomic,
)
from utils.helpers import format_inr


def render_auth_page(current_city: CityDTO) -> None:
    """Clean, dedicated authentication and registration gateway for BharatKart.
    
    Prevents unauthenticated users from accessing protected shopping, cart,
    storefront management, and order tracking.
    """
    st.markdown(
        f"""
        <div class="bk-hero" style="padding: 1.8rem 2.2rem; text-align: center; margin-bottom: 1.2rem;">
            <div class="bk-hero-eyebrow">Hyperlocal Physical Retail Marketplace · {current_city.label}</div>
            <div class="bk-hero-title" style="font-size: 2.15rem;">Welcome to BharatKart</div>
            <div class="bk-hero-desc" style="max-width: 700px; margin: 0.6rem auto 0 auto;">
                Connect directly with verified local physical stores across <strong>{current_city.name}</strong>, Bengaluru, Mumbai, Pune, and Mangalore.
                Please sign in to your account or register to start shopping.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1-Click Demo Login Shortcuts for Evaluation
    with st.container(border=True):
        st.markdown(
            """
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.4rem;">
                <span style="font-weight:700; color:#4A192C; font-size:0.95rem;">⚡ Instant Demo Account Quick-Login (1-Click Test Access):</span>
                <span class="bk-stock-ok">✓ TEST ACCOUNTS ACTIVE</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c_demo1, c_demo2, c_demo3 = st.columns(3)
        with c_demo1:
            if st.button("🛍️ Demo Customer (Pooja Sharma)", key="demo_login_customer", use_container_width=True):
                # Ensure demo customer exists
                user = authenticate_user("buyer_demo@bharatkart.in", "Buyer@123")
                if not user:
                    try:
                        req = CustomerRegistrationRequest(
                            full_name="Pooja Sharma",
                            email="buyer_demo@bharatkart.in",
                            phone="9876543210",
                            password="Buyer@123",
                            default_city_id=current_city.id,
                            default_address="Flat 402, Heritage Residency, Indiranagar",
                            pincode="560038",
                        )
                        register_or_update_customer(req)
                        user = authenticate_user("buyer_demo@bharatkart.in", "Buyer@123")
                    except Exception:
                        pass
                if user:
                    st.session_state.current_user = user
                    st.session_state.registered_customer = get_customer_by_email(user.email)
                    st.session_state.active_page = "Home"
                    st.rerun()

        with c_demo2:
            if st.button("🏬 Demo Merchant (Rohan Hegde)", key="demo_login_seller", use_container_width=True):
                user = authenticate_user("rohan@malnadroasters.in", "Seller@123")
                if user:
                    st.session_state.current_user = user
                    st.session_state.active_page = "SellerPortal"
                    st.rerun()

        with c_demo3:
            if st.button("🛡️ Super Admin (BharatKart HQ)", key="demo_login_admin", use_container_width=True):
                user = authenticate_user("admin@bharatkart.in", "Admin@123")
                if user:
                    st.session_state.current_user = user
                    st.session_state.active_page = "Operations"
                    st.rerun()

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)

    tab_signin, tab_signup, tab_merchant = st.tabs(
        ["🛍️ Customer Sign In", "📝 New Customer Registration", "🏬 Merchant & Admin Access"]
    )

    with tab_signin:
        st.markdown("### Customer Sign In")
        st.caption("Sign in with your registered email and password to access your bag, past orders, and local storefronts.")
        with st.form("auth_signin_form"):
            login_email = st.text_input("Email Address", placeholder="buyer_demo@bharatkart.in")
            login_password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Sign In to BharatKart", type="primary", use_container_width=True)

        if login_submitted:
            if not login_email or not login_password:
                st.error("Please provide both email and password.")
            else:
                user = authenticate_user(login_email.strip(), login_password)
                if user:
                    st.session_state.current_user = user
                    if user.role == "customer":
                        cust = get_customer_by_email(user.email)
                        if cust:
                            st.session_state.registered_customer = cust
                    st.session_state.active_page = "Home"
                    st.toast(f"Welcome back, {user.full_name}!", icon="👋")
                    st.rerun()
                else:
                    st.error("Invalid email or password. Please verify your credentials or register below.")

    with tab_signup:
        st.markdown("### Create New Customer Account")
        cities = get_active_cities()
        city_by_id = {c.id: c for c in cities}
        city_ids = [c.id for c in cities]
        default_idx = city_ids.index(current_city.id) if current_city.id in city_ids else 0

        with st.form("auth_signup_form"):
            c1, c2 = st.columns(2)
            with c1:
                full_name = st.text_input("Full Name *", placeholder="Aarav Sharma")
                email = st.text_input("Email Address *", placeholder="aarav@example.com")
                password = st.text_input("Create Password *", type="password", placeholder="Minimum 6 characters")
            with c2:
                phone = st.text_input("Mobile Number (10-digit) *", placeholder="9876543210")
                default_city_id = st.selectbox(
                    "Preferred Fulfillment City *",
                    options=city_ids,
                    index=default_idx,
                    format_func=lambda cid: city_by_id[cid].label,
                )

            default_address = st.text_area(
                "Default Delivery Address *",
                placeholder="House No., Street, Area...",
                height=70,
            )
            pincode = st.text_input("Pincode *", max_chars=6, placeholder="560038")

            reg_submitted = st.form_submit_button("Create Account & Start Shopping", type="primary", use_container_width=True)

        if reg_submitted:
            try:
                req = CustomerRegistrationRequest(
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    password=password,
                    default_city_id=default_city_id,
                    default_address=default_address,
                    pincode=pincode,
                )
                cust_dto = register_or_update_customer(req)
                st.session_state.registered_customer = cust_dto
                user = authenticate_user(email, password)
                if user:
                    st.session_state.current_user = user
                st.session_state.active_page = "Home"
                st.success(f"Welcome to BharatKart, {cust_dto.full_name}!")
                st.rerun()
            except ValidationError as ve:
                for err in ve.errors():
                    field = str(err["loc"][-1]).replace("_", " ").title() if err.get("loc") else "Field"
                    st.error(f"**{field}**: {err['msg']}")
            except CustomerRegistrationError as cre:
                st.error(str(cre))

    with tab_merchant:
        st.markdown("### Merchant & Administrator Portal")
        st.caption("Access the physical store management portal or administrative operations dashboard.")
        with st.form("merchant_admin_login_form"):
            m_email = st.text_input("Merchant / Admin Email ID", placeholder="rohan@malnadroasters.in")
            m_pass = st.text_input("Password", type="password")
            m_submit = st.form_submit_button("Sign In to Portal", type="primary", use_container_width=True)

        if m_submit:
            user = authenticate_user(m_email.strip(), m_pass)
            if user and user.role in ("seller", "admin"):
                st.session_state.current_user = user
                if user.role == "seller":
                    st.session_state.active_page = "SellerPortal"
                else:
                    st.session_state.active_page = "Operations"
                st.rerun()
            elif user:
                st.session_state.current_user = user
                st.session_state.active_page = "Home"
                st.rerun()
            else:
                st.error("Invalid credentials. Please verify your merchant or administrator email and password.")

        with st.expander("Register a New Physical Retail Store on BharatKart"):
            st.info("Want to onboard your brick-and-mortar retail store? Sign in or use the Seller Portal to submit your shop registration.")


def render_customer_registration_page(current_city: CityDTO) -> None:
    if st.button("← Back to Storefront"):
        navigate_to("Home")

    current_user = st.session_state.get("current_user")
    if current_user:
        st.markdown(
            f"""
            <div class="bk-hero" style="padding: 1.5rem 2rem;">
                <div class="bk-hero-eyebrow">Authenticated Account · Role: {current_user.role.upper()}</div>
                <div class="bk-hero-title" style="font-size: 1.85rem;">Hello, {current_user.full_name}</div>
                <div class="bk-hero-desc">Email: <strong>{current_user.email}</strong> · Session Active</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Log Out", type="secondary"):
            st.session_state.current_user = None
            st.session_state.registered_customer = None
            st.rerun()

        # Show order history for customer
        st.subheader("Your Order History & Tracking")
        orders = get_orders_for_customer(current_user.email)
        if orders:
            for o in orders:
                with st.expander(f"📦 Order {o.order_number} — {format_inr(o.total_amount)} ({o.status})"):
                    st.write(f"**Date:** {o.created_at.strftime('%d %b %Y, %I:%M %p UTC')} | **City:** {o.city_name}")
                    st.write(f"**Shipping Address:** {o.shipping_address} ({o.pincode})")

                    st.markdown("##### Shop-Wise Suborders & Fulfillment")
                    for sub in o.suborders:
                        st.markdown(
                            f"- Store: **{sub.shop_name}** (`{sub.shop_code}`) — Suborder: `{sub.suborder_number}` | Status: **{sub.status}** | Subtotal: {format_inr(sub.subtotal)}"
                        )
        else:
            st.info("You haven't placed any orders yet.")
        return

    tab_signin, tab_signup = st.tabs(["Buyer & Seller Sign In", "New Buyer Membership"])

    with tab_signin:
        st.markdown("### Secure Sign In")
        with st.form("signin_form"):
            login_email = st.text_input("Registered Email Address", placeholder="aarav@example.com")
            login_password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

        if login_submitted:
            user = authenticate_user(login_email, login_password)
            if user:
                st.session_state.current_user = user
                if user.role == "customer":
                    cust = get_customer_by_email(user.email)
                    if cust:
                        st.session_state.registered_customer = cust
                st.success(f"Welcome back, {user.full_name}!")
                st.rerun()
            else:
                st.error("Invalid email or password. Please verify your credentials.")

    with tab_signup:
        st.markdown("### Create Your Buyer Profile")
        cities = get_active_cities()
        city_by_id = {c.id: c for c in cities}
        city_ids = [c.id for c in cities]
        default_idx = city_ids.index(current_city.id) if current_city.id in city_ids else 0

        with st.form("customer_signup_form"):
            c1, c2 = st.columns(2)
            with c1:
                full_name = st.text_input("Full Name *", placeholder="Aarav Sharma")
                email = st.text_input("Email Address *", placeholder="aarav@example.com")
                password = st.text_input("Create Password *", type="password", placeholder="Minimum 6 characters")
            with c2:
                phone = st.text_input("Mobile Number (10-digit) *", placeholder="9876543210")
                default_city_id = st.selectbox(
                    "Preferred Delivery City *",
                    options=city_ids,
                    index=default_idx,
                    format_func=lambda cid: city_by_id[cid].label,
                )

            default_address = st.text_area(
                "Default Shipping Address *",
                placeholder="Flat 402, Heritage Residency, Indiranagar 2nd Stage",
                height=75,
            )
            pincode = st.text_input("Pincode *", max_chars=6, placeholder="560038")

            submitted = st.form_submit_button("Register & Save Profile", type="primary", use_container_width=True)

        if submitted:
            try:
                req = CustomerRegistrationRequest(
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    password=password,
                    default_city_id=default_city_id,
                    default_address=default_address,
                    pincode=pincode,
                )
                cust_dto = register_or_update_customer(req)
                st.session_state.registered_customer = cust_dto
                # Auto authenticate
                user = authenticate_user(email, password)
                if user:
                    st.session_state.current_user = user
                st.success(f"Welcome to BharatKart, {cust_dto.full_name}!")
                st.rerun()
            except ValidationError as ve:
                for err in ve.errors():
                    field = str(err["loc"][-1]).replace("_", " ").title() if err.get("loc") else "Field"
                    st.error(f"**{field}**: {err['msg']}")
            except CustomerRegistrationError as cre:
                st.error(str(cre))


def render_shop_registration_page(current_city: CityDTO) -> None:
    if st.button("← Back to Storefront"):
        navigate_to("Home")

    current_user = st.session_state.get("current_user")

    # If seller is logged in, show Seller Dashboard!
    if current_user and current_user.role == "seller":
        render_seller_dashboard(current_user, current_city)
        return

    st.markdown(
        """
        <div class="bk-hero" style="padding: 1.9rem 2.4rem;">
            <div class="bk-hero-eyebrow">BharatKart Seller Hub · Dedicated Onboarding Page</div>
            <div class="bk-hero-title" style="font-size: 2.05rem;">Sell on BharatKart</div>
            <div class="bk-hero-desc">
                Connect your actual physical retail store with buyers across Bengaluru, Mumbai, Pune, and Mangalore.
                Zero listing fees, verified customer base, same-city fulfillment.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_register, tab_login, tab_directory = st.tabs(
        ["New Shop Registration", "Seller Portal Login", "Verified Partner Stores"]
    )

    with tab_login:
        st.subheader("Partner Merchant Login")
        with st.form("seller_login_form"):
            s_email = st.text_input("Owner Email ID", placeholder="seller@yourshop.in")
            s_pass = st.text_input("Password", type="password")
            s_submit = st.form_submit_button("Log In to Seller Portal", type="primary", use_container_width=True)

        if s_submit:
            user = authenticate_user(s_email, s_pass)
            if user and user.role in ("seller", "admin"):
                st.session_state.current_user = user
                st.success(f"Authenticated as {user.full_name}!")
                st.rerun()
            else:
                st.error("Invalid seller credentials. Please try again.")

    with tab_register:
        if st.session_state.get("last_registered_shop"):
            shop = st.session_state.last_registered_shop
            st.success(
                f"**Shop Registered Successfully!** Your Partner Store ID is **`{shop.shop_code}`** "
                f"for **{shop.shop_name}** ({shop.city_name}). Status: **{shop.status}**."
            )

        cities = get_active_cities()
        city_by_id = {c.id: c for c in cities}
        city_ids = [c.id for c in cities]
        default_city_idx = city_ids.index(current_city.id) if current_city.id in city_ids else 0
        categories = get_categories()

        with st.form("shop_registration_form"):
            st.markdown('<div class="bk-step-badge">Step 1 of 4 · Shop & Owner Details</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                shop_name = st.text_input("Shop / Brand Name *", placeholder="e.g., Mysuru Heritage Crafts")
                owner_name = st.text_input("Proprietor Name *", placeholder="e.g., Ananya Rao")
                password = st.text_input("Seller Account Password *", type="password", placeholder="Minimum 6 characters")
                business_type = st.selectbox(
                    "Business Entity Type *",
                    options=[
                        "Sole Proprietorship",
                        "Partnership / LLP",
                        "Private Limited",
                        "Home Entrepreneur / Artisan",
                    ],
                )
            with c2:
                owner_email = st.text_input("Business Email ID *", placeholder="seller@yourshop.in")
                owner_phone = st.text_input("Registered Mobile Number (10-digit) *", placeholder="9876543210")
                primary_category = st.selectbox("Primary Selling Category *", options=categories)

            shop_description = st.text_area(
                "About Your Shop & Products (Optional)",
                placeholder="Tell buyers what makes your store special...",
                height=70,
            )

            st.markdown("<hr style='border-color:#DFD3C3; margin: 1.1rem 0;'>", unsafe_allow_html=True)
            st.markdown('<div class="bk-step-badge">Step 2 of 4 · Tax & Regulatory KYC</div>', unsafe_allow_html=True)
            t1, t2, t3 = st.columns(3)
            with t1:
                pan_number = st.text_input("Business / Owner PAN * (10 chars)", max_chars=10, placeholder="ABCDE1234F")
            with t2:
                gstin = st.text_input("GSTIN (15 chars — Optional if exempted)", max_chars=15, placeholder="29ABCDE1234F1Z5")
            with t3:
                fssai_license = st.text_input("FSSAI License (14 digits — Required for Groceries)", max_chars=14, placeholder="11223344556677")

            st.markdown("<hr style='border-color:#DFD3C3; margin: 1.1rem 0;'>", unsafe_allow_html=True)
            st.markdown('<div class="bk-step-badge">Step 3 of 4 · Physical Store Pickup Address</div>', unsafe_allow_html=True)
            a1, a2, a3 = st.columns([1.3, 1, 1.3])
            with a1:
                selected_city_id = st.selectbox(
                    "Fulfillment City Hub *",
                    options=city_ids,
                    index=default_city_idx,
                    format_func=lambda cid: city_by_id[cid].label,
                )
            with a2:
                pincode = st.text_input("Shop Pincode *", max_chars=6, placeholder="560001")
            with a3:
                pickup_slot = st.selectbox(
                    "Preferred Courier Pickup Slot *",
                    options=["Morning (9:00 AM – 1:00 PM)", "Afternoon (1:00 PM – 5:00 PM)", "Evening (5:00 PM – 9:00 PM)"],
                )

            shop_address = st.text_area("Complete Physical Store Address *", placeholder="Shop No. 12, Ground Floor, MG Road...", height=70)

            st.markdown("<hr style='border-color:#DFD3C3; margin: 1.1rem 0;'>", unsafe_allow_html=True)
            st.markdown('<div class="bk-step-badge">Step 4 of 4 · Settlement Bank Account</div>', unsafe_allow_html=True)
            bk1, bk2 = st.columns(2)
            with bk1:
                bank_account_holder = st.text_input("Account Holder Name *", placeholder="As per bank cheque")
                bank_account_number = st.text_input("Bank Account Number *", max_chars=18, placeholder="50200012345678")
            with bk2:
                bank_ifsc = st.text_input("IFSC Code *", max_chars=11, placeholder="HDFC0000184")
                upi_id = st.text_input("Business UPI ID (Optional)", placeholder="yourshop@okhdfcbank")

            agree = st.checkbox("I confirm all information is authentic and agree to the BharatKart Physical Merchant Agreement.")
            submitted = st.form_submit_button("Submit & Register Store", type="primary", use_container_width=True)

        if submitted:
            if not agree:
                st.error("Please agree to the BharatKart Merchant Agreement.")
            else:
                try:
                    req = ShopRegistrationRequest(
                        shop_name=shop_name,
                        owner_name=owner_name,
                        owner_email=owner_email,
                        owner_phone=owner_phone,
                        password=password,
                        business_type=business_type,
                        primary_category=primary_category,
                        gstin=gstin,
                        pan_number=pan_number,
                        fssai_license=fssai_license,
                        city_id=selected_city_id,
                        shop_address=shop_address,
                        pincode=pincode,
                        pickup_slot=pickup_slot,
                        bank_account_holder=bank_account_holder,
                        bank_account_number=bank_account_number,
                        bank_ifsc=bank_ifsc,
                        upi_id=upi_id,
                        shop_description=shop_description,
                    )
                    created_shop = register_shop_atomic(req)
                    st.session_state.last_registered_shop = created_shop
                    st.success(f"Registered {created_shop.shop_name}! Awaiting admin verification.")
                    st.rerun()
                except ValidationError as ve:
                    for err in ve.errors():
                        field = str(err["loc"][-1]).replace("_", " ").title() if err.get("loc") else "Field"
                        st.error(f"**{field}**: {err['msg']}")
                except ShopRegistrationError as sre:
                    st.error(str(sre))

    with tab_directory:
        st.subheader("Verified Partner Stores Directory")
        shops = list_registered_shops()
        st.caption(f"Total Registered Stores: {len(shops)}")
        if shops:
            table_rows = [
                {
                    "Shop Code": s.shop_code,
                    "Store Name": s.shop_name,
                    "Owner": s.owner_name,
                    "City": s.city_name,
                    "Category": s.primary_category,
                    "Status": s.status,
                }
                for s in shops
            ]
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)


def render_seller_dashboard(user, current_city: CityDTO) -> None:
    st.markdown(
        f"""
        <div class="bk-hero" style="padding: 1.6rem 2.2rem;">
            <div class="bk-hero-eyebrow">Merchant Portal · Authenticated: {user.email}</div>
            <div class="bk-hero-title" style="font-size: 2rem;">Seller Storefront Management</div>
            <div class="bk-hero-desc">Manage products, live stock, and incoming orders for your physical store.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    shop = get_shop_by_id(user.shop_id) if user.shop_id else None
    if not shop:
        # Search by owner email
        all_s = list_registered_shops()
        shop = next((s for s in all_s if s.owner_email.lower() == user.email.lower()), None)

    if not shop:
        st.warning("No store profile currently associated with this seller account.")
        return

    # Store Status Banner
    status_color = "#1B5E20" if shop.status == "VERIFIED" else "#B85D3B"
    st.markdown(
        f"""
        <div class="bk-panel" style="border-left: 4px solid {status_color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3>{shop.shop_name} ({shop.shop_code})</h3>
                <span style="color:{status_color}; font-weight:700;">● {shop.status}</span>
            </div>
            <p><strong>Physical Store:</strong> {shop.shop_address} ({shop.city_name}) | <strong>Category:</strong> {shop.primary_category}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    d_tab1, d_tab2, d_tab3 = st.tabs(["📦 My Products & Stock", "➕ Add New Product", "🚚 Incoming Orders & Suborders"])

    with d_tab1:
        st.subheader("Store Catalogue & Live Inventory")
        products = list_products_for_city(city_id=shop.city_id, shop_id=shop.id)
        if products:
            p_data = [
                {
                    "SKU": p.sku,
                    "Name": p.name,
                    "Price (₹)": float(p.price),
                    "MRP (₹)": float(p.mrp),
                    "Live Stock": p.stock_quantity,
                    "Rating": float(p.rating),
                }
                for p in products
            ]
            st.dataframe(pd.DataFrame(p_data), use_container_width=True, hide_index=True)

            # Quick Stock Update
            st.markdown("##### Quick Stock Adjustment")
            u_col1, u_col2, u_col3 = st.columns([2, 1, 1], vertical_alignment="bottom")
            with u_col1:
                sel_p = st.selectbox("Select Product", options=products, format_func=lambda x: f"{x.name} ({x.sku})")
            with u_col2:
                new_qty = st.number_input("New Stock", min_value=0, max_value=1000, value=sel_p.stock_quantity)
            with u_col3:
                if st.button("Update Stock", type="primary"):
                    update_inventory_stock(sel_p.id, shop.city_id, shop.id, int(new_qty))
                    st.success(f"Stock for '{sel_p.name}' updated to {new_qty}!")
                    st.rerun()
        else:
            st.info("No products listed under this shop yet.")

    with d_tab2:
        st.subheader("Create New Product")
        with st.form("add_product_form"):
            np_name = st.text_input("Product Title *", placeholder="e.g. Handmade Ceramic Cup")
            np_brand = st.text_input("Brand / Label *", placeholder="e.g. Mitti Craft")
            np_cat = st.selectbox("Department Category *", options=get_categories())
            np_desc = st.text_area("Product Description *", placeholder="Provide detailed specifications...")
            np_col1, np_col2, np_col3 = st.columns(3)
            with np_col1:
                np_price = st.number_input("Selling Price (₹) *", min_value=1.0, value=499.0, step=10.0)
            with np_col2:
                np_mrp = st.number_input("MRP (₹) *", min_value=1.0, value=699.0, step=10.0)
            with np_col3:
                np_stock = st.number_input("Initial Physical Stock *", min_value=0, value=15, step=1)
            np_img = st.text_input("Image URL (Unsplash or direct image link)", placeholder="https://images.unsplash.com/...")

            submitted = st.form_submit_button("Publish Product", type="primary", use_container_width=True)

        if submitted:
            try:
                p_req = ProductCreateRequest(
                    name=np_name,
                    brand=np_brand,
                    category=np_cat,
                    description=np_desc,
                    price=Decimal(str(np_price)),
                    mrp=Decimal(str(np_mrp)),
                    image_url=np_img,
                    initial_stock=int(np_stock),
                    city_id=shop.city_id,
                )
                new_prod = create_product(shop.id, p_req)
                st.success(f"Product '{new_prod.name}' ({new_prod.sku}) created and queued in Outbox for OpenSearch/Kafka!")
                st.rerun()
            except Exception as e:
                st.error(f"Error creating product: {e}")

    with d_tab3:
        st.subheader("Incoming Orders for this Store")
        suborders = get_suborders_for_shop(shop.id)
        if suborders:
            for sub in suborders:
                with st.expander(f"📦 Suborder {sub.suborder_number} — {format_inr(sub.subtotal)} [{sub.status}]"):
                    st.write(f"Placed: {sub.created_at.strftime('%d %b %Y, %I:%M %p UTC')}")
                    for item in sub.items:
                        st.write(f"• {item.quantity} × {item.product_name} ({format_inr(item.unit_price)}) = {format_inr(item.line_total)}")

                    # Status transition
                    s_c1, s_c2 = st.columns([2, 1], vertical_alignment="bottom")
                    with s_c1:
                        new_s = st.selectbox(
                            "Update Status",
                            options=["CONFIRMED", "PROCESSING", "READY_FOR_PICKUP", "SHIPPED", "DELIVERED", "CANCELLED"],
                            index=["CONFIRMED", "PROCESSING", "READY_FOR_PICKUP", "SHIPPED", "DELIVERED", "CANCELLED"].index(sub.status)
                            if sub.status in ["CONFIRMED", "PROCESSING", "READY_FOR_PICKUP", "SHIPPED", "DELIVERED", "CANCELLED"]
                            else 0,
                            key=f"status_{sub.id}",
                        )
                    with s_c2:
                        if st.button("Save Status", key=f"btn_s_{sub.id}", type="primary"):
                            update_suborder_status(sub.id, new_s, shop_id=shop.id)
                            st.success(f"Suborder {sub.suborder_number} status updated to {new_s}!")
                            st.rerun()
        else:
            st.info("No orders received yet for this store.")
