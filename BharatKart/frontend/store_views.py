from decimal import Decimal
import pandas as pd
import streamlit as st
from backend.schemas import CityDTO
from frontend.components import add_item_to_cart, navigate_to, render_product_card
from services.opensearch_service import opensearch_manager
from services.product_service import get_categories, get_product_detail, list_products_for_city
from services.shop_service import get_shop_by_id, list_registered_shops
from utils.config import settings
from utils.helpers import (
    format_inr,
    get_offline_fallback_png,
    get_product_gallery_photos,
    get_product_photo_url,
    get_shop_cover_url,
)


def render_home_page(city: CityDTO) -> None:
    s_col1, s_col2 = st.columns([5, 1.2], vertical_alignment="bottom")
    with s_col1:
        query = st.text_input(
            "Search BharatKart",
            value=st.session_state.global_search,
            placeholder=f"Search artisan homeware, electronics, single-estate coffee in {city.name}...",
            label_visibility="collapsed",
        )
    with s_col2:
        if st.button("Search", type="primary", use_container_width=True, key="home_search_btn"):
            st.session_state.global_search = query
            navigate_to("Catalogue")

    st.markdown(
        f"""
        <div class="bk-hero">
            <div class="bk-hero-eyebrow">Hyperlocal Fulfillment · {city.label}</div>
            <div class="bk-hero-title">Crafted Goods from Actual Physical Stores.</div>
            <div class="bk-hero-desc">
                Connect with verified local brick-and-mortar merchants across <strong>{city.name}</strong>.
                Browse individual shop storefronts, combine items from multiple shops in one cart, and enjoy same-city dispatch.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Shop by Department")
    categories = get_categories()
    cat_cols = st.columns(len(categories))
    for idx, cat in enumerate(categories):
        with cat_cols[idx]:
            if st.button(cat, key=f"home_cat_{cat}", use_container_width=True):
                st.session_state.global_search = ""
                navigate_to("Catalogue", category=cat)

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

    # Local Physical Shops Discovery Section
    sh_head, sh_all = st.columns([4, 1.3], vertical_alignment="center")
    with sh_head:
        st.subheader(f"🏬 Local Physical Retail Stores in {city.name}")
    with sh_all:
        if st.button("All City Stores →", use_container_width=True, key="home_view_shops"):
            navigate_to("Shops")

    local_shops = list_registered_shops(city_id=city.id, status="VERIFIED")
    if local_shops:
        s_cols = st.columns(min(len(local_shops), 3))
        for idx, shop in enumerate(local_shops[:3]):
            shop_prods = list_products_for_city(city_id=city.id, shop_id=shop.id)[:3]
            cover_url = get_shop_cover_url(shop.shop_code)
            with s_cols[idx]:
                st.markdown(
                    f"""
                    <div class="bk-panel" style="min-height: 280px; padding: 0.8rem; display: flex; flex-direction: column; justify-content: space-between;">
                        <div>
                            <div style="height: 125px; overflow: hidden; border-radius: 6px; margin-bottom: 0.5rem; background-color: #F3ECE1;">
                                <img src="{cover_url}" alt="{shop.shop_name}" style="width: 100%; height: 100%; object-fit: cover;" />
                            </div>
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.2rem;">
                                <span class="bk-card-brand">{shop.primary_category} · {shop.city_name}</span>
                                <span class="bk-stock-ok" style="font-size:0.72rem; padding: 1px 6px;">✓ VERIFIED STORE</span>
                            </div>
                            <h4 style="margin: 0.2rem 0; color: #4A192C;">{shop.shop_name}</h4>
                            <div style="font-size: 0.8rem; color: #59524B; margin-bottom: 0.25rem;">
                                📍 {shop.shop_address}
                            </div>
                            <div style="font-size: 0.78rem; color: #59524B; margin-bottom: 0.4rem;">
                                🚚 Daily Courier Pickup: <strong>{shop.pickup_slot}</strong>
                            </div>
                            <div style="font-size: 0.82rem; color: #22201E; margin-bottom: 0.5rem;">
                                {shop.shop_description[:90] if shop.shop_description else 'Verified BharatKart partner store.'}...
                            </div>
                        </div>
                    """,
                    unsafe_allow_html=True,
                )
                if shop_prods:
                    st.caption("Available in Store:")
                    p_prev_cols = st.columns(len(shop_prods))
                    for p_idx, sprod in enumerate(shop_prods):
                        with p_prev_cols[p_idx]:
                            st.markdown(
                                f"""
                                <div style="text-align: center;">
                                    <img src="{sprod.image_url}" alt="{sprod.name}" style="width: 100%; height: 46px; object-fit: cover; border-radius: 4px; border: 1px solid #DFD3C3;" />
                                    <div style="font-size: 0.72rem; font-weight: 600; color: #4A192C; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{format_inr(sprod.price)}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                if st.button("Visit Storefront →", key=f"home_shop_{shop.id}", use_container_width=True, type="primary"):
                    navigate_to("ShopStorefront", shop_id=shop.id)
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info(f"No registered partner shops found in {city.name} yet.")

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

    st.subheader(f"Featured in {city.name}")
    featured = list_products_for_city(city_id=city.id, only_featured=True)
    if featured:
        cols = st.columns(4)
        for idx, prod in enumerate(featured[:4]):
            with cols[idx % 4]:
                render_product_card(prod, key_prefix="home_feat")

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

    h_left, h_right = st.columns([4, 1.3], vertical_alignment="center")
    with h_left:
        st.subheader("Popular Across Stores")
    with h_right:
        if st.button("Explore Full Catalogue →", use_container_width=True, key="home_view_all"):
            navigate_to("Catalogue", category="All")

    popular = list_products_for_city(city_id=city.id, sort_by="Top Rated")
    # Present 8 diverse products across distinct artisan categories and merchants
    distinct_popular = []
    seen_titles = set()
    for prod in popular:
        norm_title = prod.name.strip().lower()
        if norm_title not in seen_titles:
            seen_titles.add(norm_title)
            distinct_popular.append(prod)
        if len(distinct_popular) == 8:
            break

    pop_cols = st.columns(4)
    for idx, prod in enumerate(distinct_popular):
        with pop_cols[idx % 4]:
            render_product_card(prod, key_prefix="home_pop")


def render_shops_directory_page(city: CityDTO) -> None:
    st.title(f"🏬 Local Physical Retail Stores — {city.label}")
    st.markdown(
        "Explore verified neighbourhood physical retail shops. Open any store's dedicated storefront to browse exclusively their in-stock products. "
        "All catalog records are grounded in live database inventory."
    )

    shops = list_registered_shops(city_id=city.id, status="VERIFIED")
    if not shops:
        st.warning(f"No verified physical shops found currently in {city.name}.")
        return

    cols = st.columns(2)
    for idx, shop in enumerate(shops):
        cover_url = get_shop_cover_url(shop.shop_code)
        shop_prods = list_products_for_city(city_id=city.id, shop_id=shop.id)[:3]
        with cols[idx % 2]:
            st.markdown(
                f"""
                <div class="bk-panel" style="padding: 1rem; margin-bottom: 1rem;">
                    <div style="height: 140px; overflow: hidden; border-radius: 6px; margin-bottom: 0.6rem; background-color: #F3ECE1;">
                        <img src="{cover_url}" alt="{shop.shop_name}" style="width: 100%; height: 100%; object-fit: cover;" />
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.25rem;">
                        <span class="bk-card-brand">{shop.primary_category} · {shop.city_name}</span>
                        <span class="bk-stock-ok">✓ VERIFIED STORE</span>
                    </div>
                    <h3 style="margin: 0.2rem 0; color: #4A192C;">{shop.shop_name}</h3>
                    <div style="font-size: 0.85rem; color: #59524B; margin-bottom: 0.35rem;">
                        Proprietor: <strong>{shop.owner_name}</strong> ({shop.business_type}) · Code: <code>{shop.shop_code}</code>
                    </div>
                    <div style="font-size: 0.85rem; color: #22201E; margin-bottom: 0.5rem;">
                        {shop.shop_description or 'Specialist local physical retailer offering verified same-city fulfillment.'}
                    </div>
                    <div style="font-size: 0.8rem; color: #59524B; line-height: 1.5; margin-bottom: 0.5rem;">
                        📍 <strong>Store Address:</strong> {shop.shop_address} ({shop.pincode})<br>
                        🚚 <strong>Daily Courier Pickup Slot:</strong> {shop.pickup_slot}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if shop_prods:
                st.caption(f"In-Store Products from {shop.shop_name}:")
                p_cols = st.columns(len(shop_prods))
                for pi, sp in enumerate(shop_prods):
                    with p_cols[pi]:
                        st.markdown(
                            f"""
                            <div style="text-align:center;">
                                <img src="{sp.image_url}" alt="{sp.name}" style="width:100%; height:50px; object-fit:cover; border-radius:4px; border:1px solid #DFD3C3;" />
                                <div style="font-size:0.75rem; font-weight:600; color:#4A192C;">{format_inr(sp.price)}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
            b1, _ = st.columns([1.5, 2])
            with b1:
                if st.button(f"Enter {shop.shop_name} →", key=f"dir_visit_{shop.id}", type="primary"):
                    navigate_to("ShopStorefront", shop_id=shop.id)


def render_shop_storefront_page(city: CityDTO) -> None:
    shop_id = st.session_state.get("selected_shop_id")
    if not shop_id:
        st.error("No store selected.")
        if st.button("← Back to Shops"):
            navigate_to("Shops")
        return

    shop = get_shop_by_id(shop_id)
    if not shop:
        st.error("Store profile not found.")
        return

    if st.button("← Back to All Stores"):
        navigate_to("Shops")

    cover_url = get_shop_cover_url(shop.shop_code)
    st.markdown(
        f"""
        <div class="bk-hero" style="padding: 1.8rem 2.2rem; background: linear-gradient(rgba(74, 25, 44, 0.88), rgba(51, 16, 30, 0.94)), url('{cover_url}'); background-size: cover; background-position: center;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div class="bk-hero-eyebrow" style="color: #DFD3C3;">Verified Local Merchant · Store ID: {shop.shop_code}</div>
                <span class="bk-stock-ok" style="font-size:0.75rem; background-color:rgba(255,255,255,0.2); color:#FAF7F2; border:1px solid #DFD3C3;">✓ VERIFIED MERCHANT</span>
            </div>
            <div class="bk-hero-title" style="font-size: 2.2rem; color: #FAF7F2;">{shop.shop_name}</div>
            <div class="bk-hero-desc" style="color: #F3ECE1;">
                {shop.shop_description or 'Authentic local retailer on BharatKart.'}<br>
                📍 <strong>Store Address:</strong> {shop.shop_address} ({shop.city_name}) · <strong>Proprietor:</strong> {shop.owner_name} ({shop.business_type})<br>
                🚚 <strong>Daily Courier Pickup Slot:</strong> {shop.pickup_slot}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    f1, f2 = st.columns([3, 1.2], vertical_alignment="bottom")
    with f1:
        s_query = st.text_input("Search within this shop", placeholder=f"Search items from {shop.shop_name}...")
    with f2:
        in_stock_only = st.checkbox("In Stock Only", value=False, key="storefront_stock_filter")

    products = list_products_for_city(
        city_id=city.id,
        shop_id=shop.id,
        search_query=s_query,
        in_stock_only=in_stock_only,
    )

    # If no products in currently selected fulfillment city, check shop's home city
    is_home_city_fallback = False
    if not products and city.id != shop.city_id:
        home_products = list_products_for_city(
            city_id=shop.city_id,
            shop_id=shop.id,
            search_query=s_query,
            in_stock_only=in_stock_only,
        )
        if home_products:
            products = home_products
            is_home_city_fallback = True

    if is_home_city_fallback:
        st.info(f"Showing {len(products)} product(s) available from **{shop.shop_name}** in its flagship store in **{shop.city_name}**.")
    else:
        st.caption(f"Showing {len(products)} product(s) offered exclusively by {shop.shop_name} in {city.name}")

    if not products:
        st.info("No products currently listed for this shop in the selected city.")
        return

    cols = st.columns(4)
    for idx, prod in enumerate(products):
        with cols[idx % 4]:
            render_product_card(prod, key_prefix=f"sf_{shop.id}")


def render_catalogue_page(city: CityDTO) -> None:
    st.title(f"Catalogue — {city.label}")

    categories = ["All"] + get_categories()
    if st.session_state.selected_category not in categories:
        st.session_state.selected_category = "All"

    shops = list_registered_shops(city_id=city.id, status="VERIFIED")
    shop_options = [None] + [s.id for s in shops]
    shop_labels = {None: "All Partner Stores"}
    for s in shops:
        shop_labels[s.id] = f"🏬 {s.shop_name}"

    f1, f2, f3, f4, f5 = st.columns([2.4, 1.4, 1.5, 1.3, 1.1], vertical_alignment="bottom")
    with f1:
        search_input = st.text_input(
            "Search products, brands, or descriptions",
            value=st.session_state.global_search,
            placeholder="e.g., Earbuds, Brass, Coffee, Sandalwood...",
        )
        st.session_state.global_search = search_input
    with f2:
        chosen_cat = st.selectbox(
            "Category",
            options=categories,
            index=categories.index(st.session_state.selected_category),
        )
        st.session_state.selected_category = chosen_cat
    with f3:
        chosen_shop = st.selectbox(
            "Physical Store",
            options=shop_options,
            format_func=lambda sid: shop_labels.get(sid, "All Stores"),
        )
    with f4:
        sort_by = st.selectbox(
            "Sort By",
            options=["Featured", "Price: Low to High", "Price: High to Low", "Top Rated", "Availability"],
        )
    with f5:
        in_stock_only = st.checkbox("In Stock Only", value=False)

    products = list_products_for_city(
        city_id=city.id,
        shop_id=chosen_shop,
        search_query=search_input,
        category=chosen_cat,
        sort_by=sort_by,
        in_stock_only=in_stock_only,
    )

    st.caption(f"Showing {len(products)} product(s) available for fulfillment in {city.label}")

    if not products:
        st.markdown(
            """
            <div class="bk-panel" style="text-align: center; padding: 2.5rem;">
                <h3>No matching products found</h3>
                <p style="color: #59524B;">Try clearing your search filters or exploring another local department.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Reset Filters", type="primary"):
            st.session_state.global_search = ""
            st.session_state.selected_category = "All"
            st.rerun()
        return

    cols = st.columns(4)
    for idx, prod in enumerate(products):
        with cols[idx % 4]:
            render_product_card(prod, key_prefix="cat")


def render_product_details_page(city: CityDTO) -> None:
    if st.button("← Back to Catalogue"):
        navigate_to("Catalogue")

    pid = st.session_state.selected_product_id
    if not pid:
        st.info("Select a product from the catalogue to view details.")
        return

    product = get_product_detail(product_id=pid, city_id=city.id)
    if not product:
        st.error("Product not found for the selected city.")
        return

    left, right = st.columns([1.15, 1.35], gap="large")
    fallback_uri = get_offline_fallback_png(product.sku, product.category)

    # Multi-angle photo gallery
    gallery_photos = get_product_gallery_photos(product.sku)
    photo_key = f"pdp_photo_idx_{product.id}"
    if photo_key not in st.session_state:
        st.session_state[photo_key] = 0
    active_photo_idx = st.session_state[photo_key]
    if active_photo_idx >= len(gallery_photos):
        active_photo_idx = 0
    active_photo_url = gallery_photos[active_photo_idx]

    with left:
        st.markdown(
            f"""
            <div class="bk-panel" style="padding: 0.8rem;">
                <img src="{active_photo_url}"
                     onerror="this.onerror=null; this.src='{fallback_uri}';"
                     alt="{product.name}"
                     style="width: 100%; height: 410px; object-fit: cover; border-radius: 8px;"/>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if len(gallery_photos) > 1:
            st.caption("Inspect Multi-Angle Photographs:")
            t_cols = st.columns(len(gallery_photos))
            for t_idx, t_url in enumerate(gallery_photos):
                with t_cols[t_idx]:
                    border_style = "2.5px solid #8C3A27" if t_idx == active_photo_idx else "1px solid #DFD3C3"
                    st.markdown(
                        f"""
                        <div style="cursor:pointer;">
                            <img src="{t_url}" style="width:100%; height:55px; object-fit:cover; border-radius:4px; border:{border_style};" />
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(f"View {t_idx+1}", key=f"pdp_thumb_{product.id}_{t_idx}", use_container_width=True):
                        st.session_state[photo_key] = t_idx
                        st.rerun()

    with right:
        st.markdown(
            f'<div class="bk-card-brand">{product.category} · {product.brand} · SKU: {product.sku}</div>',
            unsafe_allow_html=True,
        )
        st.title(product.name)

        if product.shop_name:
            st.markdown(
                f"""
                <div style="background-color: #F8F5F0; border-left: 3px solid #8C3A27; padding: 0.55rem 0.85rem; margin: 0.5rem 0 1rem 0; border-radius: 4px;">
                    🏬 Sold & Dispatched by verified store: <strong>{product.shop_name}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if product.shop_id and st.button(f"Visit {product.shop_name} Storefront →", key="pdp_visit_store"):
                navigate_to("ShopStorefront", shop_id=product.shop_id)

        st.markdown(f"**Customer Rating:** ★ {product.rating} / 5.00 · <span class='bk-stock-ok'>✓ Verified Customer Reviews</span>", unsafe_allow_html=True)

        # Handle Variants
        price_to_display = Decimal(product.price)
        if product.variants:
            st.markdown("#### Select Variant / Specification")
            var_labels = []
            for v in product.variants:
                adj = v.price_adjustment
                adj_str = f" (+{format_inr(adj)})" if adj > Decimal("0") else (f" (-{format_inr(abs(adj))})" if adj < Decimal("0") else " (Standard)")
                var_labels.append(f"{v.variant_name}: {v.variant_value}{adj_str}")

            chosen_var = st.radio("Available Options", options=var_labels, horizontal=True)
            sel_idx = var_labels.index(chosen_var)
            active_variant = product.variants[sel_idx]
            price_to_display = Decimal(product.price) + Decimal(active_variant.price_adjustment)

        discount_tag = (
            f'<span class="bk-discount">Save {product.discount_percent}%</span>'
            if product.discount_percent > 0
            else ""
        )
        st.markdown(
            f"""
            <div class="bk-price-row" style="margin: 1rem 0;">
                <span class="bk-price" style="font-size: 1.65rem;">{format_inr(price_to_display)}</span>
                <span class="bk-mrp" style="font-size: 1.05rem;">{format_inr(product.mrp)}</span>
                {discount_tag}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if product.stock_quantity > settings.LOW_STOCK_THRESHOLD:
            stock_msg = f"<span class='bk-stock-ok'>{product.stock_quantity} units ready in {product.city_name}</span>"
        elif product.stock_quantity > 0:
            stock_msg = f"<span class='bk-stock-low'>Only {product.stock_quantity} left in {product.city_name}!</span>"
        else:
            stock_msg = f"<span class='bk-stock-out'>Currently Out of Stock in {product.city_name}</span>"

        st.markdown(
            f"""
            <div class="bk-panel">
                <div style="margin-bottom: 0.4rem;"><strong>Fulfillment Hub:</strong> {product.city_name}</div>
                <div><strong>Live Physical Store Stock:</strong> {stock_msg}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write(product.description)
        st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

        if product.stock_quantity > 0:
            already_in_cart = st.session_state.cart.get(product.id, 0)
            max_addable = max(0, product.stock_quantity - already_in_cart)

            if max_addable == 0:
                st.warning(f"You already have all {product.stock_quantity} available units in your cart.")
                if st.button("Go to Shopping Bag", type="primary"):
                    navigate_to("Cart")
            else:
                q_col, b_col = st.columns([1, 2], vertical_alignment="bottom")
                with q_col:
                    qty = st.number_input(
                        "Quantity",
                        min_value=1,
                        max_value=max_addable,
                        value=1,
                        step=1,
                        key=f"pdp_qty_{product.id}",
                    )
                with b_col:
                    if st.button("Add to Shopping Bag", type="primary", use_container_width=True):
                        add_item_to_cart(product, int(qty))
                        st.rerun()
        else:
            st.button("Out of Stock in Selected City", disabled=True, use_container_width=True)
