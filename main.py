import base64
import streamlit as st
import pandas as pd
from datetime import date

import db

st.set_page_config(page_title="StayOps Prototype", layout="wide")

# ----------------- CONFIG -----------------
OWNER_SHARE = 0.65
OPERATOR_SHARE = 0.25
PLATFORM_SHARE = 0.10

# ----------------- UI STATE INIT -----------------
for _key, _default in [
    ("selected_property_id", None),
    ("pending_payment_booking_id", None),
    ("payment_just_completed", False),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ----------------- FETCH DATA -----------------
properties = db.get_properties()
bookings   = db.get_bookings()
users      = db.get_users()
expenses   = db.get_expenses()

# ----------------- PURE HELPERS -----------------
def get_expenses_for_booking(booking_id: int) -> float:
    return float(sum(e["amount"] for e in expenses if e["booking_id"] == booking_id))

def has_conflict(property_id: int, check_in: date, check_out: date) -> bool:
    for b in bookings:
        if b["property_id"] != property_id:
            continue
        if b.get("status") == "cancelled":
            continue
        if check_in < b["check_out"] and check_out > b["check_in"]:
            return True
    return False

def compute_split(price_total: float, exp: float):
    net = max(price_total - exp, 0.0)
    return net, net * OWNER_SHARE, net * OPERATOR_SHARE, net * PLATFORM_SHARE

def summarize_for_owner(owner_id: int):
    prop_ids = {p["id"] for p in properties if p["owner_id"] == owner_id}
    total_bookings, total_owner = 0, 0.0
    for b in bookings:
        if b["property_id"] in prop_ids:
            _, owner_amt, _, _ = compute_split(b["price_total"], get_expenses_for_booking(b["id"]))
            total_bookings += 1
            total_owner += owner_amt
    return total_bookings, total_owner

def summarize_for_operator(operator_id: int):
    prop_ids = {p["id"] for p in properties if p["operator_id"] == operator_id}
    total_bookings, total_op = 0, 0.0
    for b in bookings:
        if b["property_id"] in prop_ids:
            _, _, op_amt, _ = compute_split(b["price_total"], get_expenses_for_booking(b["id"]))
            total_bookings += 1
            total_op += op_amt
    return total_bookings, total_op

# ----------------- UI LAYOUT -----------------
st.title("StayOps – Pool Villa Platform")
st.caption("Owner ↔ Operator ↔ Guest with date-based booking & profit sharing")

tab_guest, tab_owner, tab_operator, tab_payout = st.tabs(
    ["🏡 Guest (Airbnb-style)", "👑 Owner", "🧑‍🔧 Operator", "💰 Payout Summary"]
)

# ---------- TAB 1: GUEST ----------
with tab_guest:
    if st.session_state.get("payment_just_completed"):
        st.markdown("## ✅ Payment Successful!")
        st.success("Your booking has been confirmed. Thank you for your reservation!")
        st.balloons()
        if st.button("← Back to main page", key="back_after_payment"):
            st.session_state.payment_just_completed = False
            st.rerun()

    elif st.session_state.pending_payment_booking_id is not None:
        pay_bid = st.session_state.pending_payment_booking_id
        pay_booking = next(b for b in bookings if b["id"] == pay_bid)
        pay_prop = next(p for p in properties if p["id"] == pay_booking["property_id"])

        st.markdown("## 💳 Complete your payment")
        st.markdown("---")
        pay_left, pay_right = st.columns([1, 1])

        with pay_left:
            st.markdown("### Booking Summary")
            st.write(f"🏡 **{pay_prop['name']}**")
            st.write(f"📍 {pay_prop['location']}")
            st.write(f"👤 Guest: {pay_booking['guest_name']}")
            st.write(f"📅 {pay_booking['check_in']} → {pay_booking['check_out']} ({pay_booking['nights']} nights)")
            st.markdown(f"### Total: **{pay_booking['price_total']:.0f} THB**")

        with pay_right:
            st.markdown("### Card Details")
            card_name   = st.text_input("Cardholder name", key="pay_card_name")
            card_number = st.text_input("Card number", placeholder="•••• •••• •••• ••••", max_chars=19, key="pay_card_number")
            card_expiry = st.text_input("Expiry (MM/YY)", max_chars=5, key="pay_expiry")
            card_cvv    = st.text_input("CVV", max_chars=4, key="pay_cvv")

            if st.button(f"Pay {pay_booking['price_total']:.0f} THB", key="pay_now"):
                digits = card_number.replace(" ", "").replace("-", "")
                if not all([card_name.strip(), card_number.strip(), card_expiry.strip(), card_cvv.strip()]):
                    st.error("Please fill in all card details.")
                elif not digits.isdigit() or not (13 <= len(digits) <= 19):
                    st.error("Please enter a valid card number.")
                else:
                    db.update_booking_status(pay_bid, "paid")
                    st.session_state.pending_payment_booking_id = None
                    st.session_state.payment_just_completed = True
                    st.rerun()

            if st.button("Cancel payment", key="pay_cancel"):
                st.session_state.pending_payment_booking_id = None
                st.rerun()

    elif st.session_state.selected_property_id is not None:
        prop = next(p for p in properties if p["id"] == st.session_state.selected_property_id)

        if st.button("← Back to listings"):
            st.session_state.selected_property_id = None
            st.rerun()

        st.markdown("## Selected stay")
        left, right = st.columns([2, 1])

        with left:
            st.image(prop["image_url"], use_container_width=True)
            st.markdown(f"### {prop['name']}")
            st.write(f"📍 {prop['location']}")
            st.write(
                f"⭐ {prop['rating']} · {prop['reviews']} reviews · "
                f"{prop['guests']} guests · {prop['bedrooms']} bedrooms · {prop['baths']} baths"
            )
            st.markdown("#### About this place")
            st.write(prop["description"])

        with right:
            st.markdown("#### Reserve")
            check_in    = st.date_input("Check-in date", value=date.today(), key="detail_check_in")
            check_out   = st.date_input("Check-out date", value=date.today(), key="detail_check_out")
            guest_name  = st.text_input("Guest name", value="Demo Guest", key="detail_guest_name")
            guest_count = st.number_input("Number of guests", min_value=1, max_value=16, value=2, key="detail_guests")

            nights = (check_out - check_in).days
            if nights <= 0:
                st.error("Check-out must be after check-in.")
                est_price = 0
            else:
                est_price = prop["nightly_rate"] * nights

            st.markdown(f"**{prop['nightly_rate']:.0f} THB x {max(nights,0)} nights = {est_price:.0f} THB**")

            if st.button("Create booking", key="detail_create_booking"):
                if nights <= 0:
                    st.error("Cannot create booking: invalid dates.")
                elif guest_count > prop["guests"]:
                    st.error(f"This villa fits max {prop['guests']} guests.")
                elif has_conflict(prop["id"], check_in, check_out):
                    st.error("These dates are already booked. Please choose different dates.")
                else:
                    price_total = prop["nightly_rate"] * nights
                    bid = db.add_booking(prop["id"], guest_name, check_in, check_out, nights, price_total)
                    st.session_state.selected_property_id = None
                    st.session_state.pending_payment_booking_id = bid
                    st.rerun()

    else:
        st.subheader("Find your wellness & pet-friendly pool villa in Khao Yai")

        with st.container():
            col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 1])
            with col_a:
                search_location = st.text_input("Location", value="Khao Yai", key="search_location")
            with col_b:
                search_check_in  = st.date_input("Check in", value=date.today(), key="search_check_in")
            with col_c:
                search_check_out = st.date_input("Check out", value=date.today(), key="search_check_out")
            with col_d:
                search_guests = st.number_input("Guests", min_value=1, max_value=16, value=1, key="search_guests")

        st.markdown("---")
        st.markdown("### Stays in Khao Yai")

        props_df = pd.DataFrame(properties)
        if props_df.empty:
            st.info("No properties available yet.")
        else:
            filtered_df = props_df[
                (props_df["guests"] >= search_guests) &
                (props_df["location"].str.contains(search_location, case=False, na=False))
            ]

            if search_check_out > search_check_in:
                filtered_df = filtered_df[
                    ~filtered_df["id"].apply(
                        lambda pid: has_conflict(pid, search_check_in, search_check_out)
                    )
                ]
            elif search_check_out == search_check_in:
                st.warning("Check-out must be after check-in to filter by availability.")

            if filtered_df.empty:
                st.info("No properties match your search. Try adjusting your filters.")

            for _, row in filtered_df.iterrows():
                with st.container():
                    col1, col2 = st.columns([1.2, 2])
                    with col1:
                        st.image(row["image_url"], use_container_width=True)
                    with col2:
                        st.markdown(f"#### {row['name']}")
                        st.write(f"📍 {row['location']}")
                        st.write(
                            f"⭐ {row['rating']} · {row['reviews']} reviews · "
                            f"{int(row['guests'])} guests · {int(row['bedrooms'])} bedrooms · {int(row['baths'])} baths"
                        )
                        st.write(f"💰 **{row['nightly_rate']:.0f} THB / night**")
                        if st.button("View details", key=f"view_{row['id']}"):
                            st.session_state.selected_property_id = int(row["id"])
                            st.rerun()
                st.markdown("---")

# ---------- TAB 2: OWNER ----------
with tab_owner:
    st.subheader("Owner: manage profile & add pool villas")

    users_df     = pd.DataFrame(users)
    owners_df    = users_df[users_df["role"] == "owner"] if not users_df.empty else pd.DataFrame()
    operators_df = users_df[users_df["role"] == "operator"] if not users_df.empty else pd.DataFrame()

    st.markdown("### Existing Owners")
    st.dataframe(owners_df, use_container_width=True)

    st.markdown("### Add new owner")
    new_owner_name = st.text_input("New owner name")
    if st.button("Create owner"):
        if new_owner_name.strip():
            oid = db.add_user(new_owner_name.strip(), "owner")
            st.success(f"Owner created with ID: {oid}")
            st.rerun()
        else:
            st.warning("Please enter a name.")

    st.markdown("---")
    st.markdown("### Add new pool villa")

    if owners_df.empty or operators_df.empty:
        st.info("Need at least 1 owner and 1 operator to add a property.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            pname        = st.text_input("Property name", value="New Khao Yai Pool Villa")
            ploc         = st.text_input("Location", value="Khao Yai, Thailand")
            nightly_rate = st.number_input("Nightly rate (THB)", min_value=1000.0, step=500.0, value=5000.0)
        with col2:
            owner_id = st.selectbox(
                "Owner",
                owners_df["id"],
                format_func=lambda i: owners_df[owners_df.id == i]["name"].iloc[0]
            )
            operator_id = st.selectbox(
                "Operator",
                operators_df["id"],
                format_func=lambda i: operators_df[operators_df.id == i]["name"].iloc[0]
            )

        st.markdown("**Villa image (optional)**")
        _slot = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"], key="villa_img_1")
        img_bytes = _slot.read() if _slot is not None else None
        if img_bytes:
            st.image(img_bytes, width=160)

        if st.button("Add pool villa"):
            if img_bytes:
                ext = _slot.name.rsplit(".", 1)[-1].lower()
                mime = "image/png" if ext == "png" else "image/jpeg"
                image_url = f"data:{mime};base64,{base64.b64encode(img_bytes).decode()}"
            else:
                image_url = db.DEFAULT_IMAGE
            pid = db.add_property(pname, ploc, int(owner_id), int(operator_id), float(nightly_rate), image_url=image_url)
            st.success(f"🏡 New property created with ID: {pid}")
            st.rerun()

    st.markdown("### All properties")
    st.dataframe(pd.DataFrame(properties), use_container_width=True)

    st.markdown("---")
    st.markdown("### Bookings by owner")

    if owners_df.empty:
        st.info("No owners yet.")
    else:
        selected_owner_id = st.selectbox(
            "Select owner",
            owners_df["id"],
            format_func=lambda i: owners_df[owners_df.id == i]["name"].iloc[0],
            key="owner_bookings_select"
        )
        owner_prop_ids = [p["id"] for p in properties if p["owner_id"] == selected_owner_id]
        bookings_df = pd.DataFrame(bookings)
        if not bookings_df.empty and owner_prop_ids:
            owner_bookings = bookings_df[bookings_df["property_id"].isin(owner_prop_ids)].copy()
            if owner_bookings.empty:
                st.info("No bookings for this owner's properties yet.")
            else:
                props_lookup = {p["id"]: p["name"] for p in properties}
                owner_bookings["property_name"] = owner_bookings["property_id"].map(props_lookup)
                st.dataframe(
                    owner_bookings[["id", "property_name", "guest_name", "check_in", "check_out", "nights", "price_total", "status"]],
                    use_container_width=True,
                )
        else:
            st.info("No bookings for this owner's properties yet.")

# ---------- TAB 3: OPERATOR ----------
with tab_operator:
    st.subheader("Housekeeper Dashboard")

    users_df     = pd.DataFrame(users)
    operators_df = users_df[users_df["role"] == "operator"] if not users_df.empty else pd.DataFrame()

    if operators_df.empty:
        st.info("No housekeepers registered yet.")
    else:
        op_id = st.selectbox(
            "Who are you?",
            operators_df["id"],
            format_func=lambda i: operators_df[operators_df.id == i]["name"].iloc[0],
            key="hk_select"
        )

        assigned_props = [p for p in properties if p["operator_id"] == op_id]

        st.markdown("### Your assigned properties")

        if not assigned_props:
            st.info("You have no properties assigned to you yet.")
        else:
            today = date.today()

            for prop in assigned_props:
                prop_bookings = [
                    b for b in bookings
                    if b["property_id"] == prop["id"]
                    and b.get("status") not in ("cancelled",)
                    and b["check_out"] >= today
                ]
                prop_bookings.sort(key=lambda b: b["check_in"])
                next_booking = prop_bookings[0] if prop_bookings else None
                urgent = next_booking and (next_booking["check_in"] - today).days <= 1

                col1, col2, col3 = st.columns([3, 1.5, 1.5])
                with col1:
                    st.markdown(f"**{prop['name']}**")
                    st.caption(prop["location"])

                    if next_booking:
                        days_until = (next_booking["check_in"] - today).days
                        if next_booking["check_in"] <= today <= next_booking["check_out"]:
                            st.info(
                                f"🏠 **Guest in-house:** {next_booking['guest_name']}  \n"
                                f"📅 {next_booking['check_in']} → {next_booking['check_out']} "
                                f"({next_booking['nights']} nights)"
                            )
                        elif days_until == 0:
                            st.warning(
                                f"⚡ **Check-in TODAY:** {next_booking['guest_name']}  \n"
                                f"📅 {next_booking['check_in']} → {next_booking['check_out']} "
                                f"({next_booking['nights']} nights)"
                            )
                        elif days_until == 1:
                            st.warning(
                                f"⏰ **Check-in TOMORROW:** {next_booking['guest_name']}  \n"
                                f"📅 {next_booking['check_in']} → {next_booking['check_out']} "
                                f"({next_booking['nights']} nights)"
                            )
                        else:
                            st.info(
                                f"📋 **Next booking in {days_until} days:** {next_booking['guest_name']}  \n"
                                f"📅 {next_booking['check_in']} → {next_booking['check_out']} "
                                f"({next_booking['nights']} nights)"
                            )
                        if len(prop_bookings) > 1:
                            with st.expander(f"All upcoming bookings ({len(prop_bookings)})"):
                                for b in prop_bookings:
                                    st.write(
                                        f"• {b['guest_name']}: {b['check_in']} → {b['check_out']} "
                                        f"({b['nights']} nights) — *{b['status']}*"
                                    )
                    else:
                        st.caption("No upcoming bookings.")

                with col2:
                    if prop["cleaning_status"] == "clean":
                        st.success("🟢 Clean")
                    else:
                        st.error("🔴 Needs Cleaning" + (" ⚠️ Urgent!" if urgent else ""))

                with col3:
                    if prop["cleaning_status"] == "clean":
                        if st.button("Mark as Needs Cleaning", key=f"hk_toggle_{prop['id']}"):
                            db.set_cleaning_status(prop["id"], "needs_cleaning")
                            st.rerun()
                    else:
                        if st.button("Mark as Clean", key=f"hk_toggle_{prop['id']}"):
                            db.set_cleaning_status(prop["id"], "clean")
                            st.rerun()
                st.markdown("---")

    st.markdown("### Add new housekeeper")
    new_operator_name = st.text_input("New housekeeper name")
    if st.button("Create housekeeper"):
        if new_operator_name.strip():
            oid = db.add_user(new_operator_name.strip(), "operator")
            st.success(f"Housekeeper created with ID: {oid}")
            st.rerun()
        else:
            st.warning("Please enter a name.")

# ---------- TAB 4: PAYOUT SUMMARY ----------
with tab_payout:
    st.subheader("💰 Payout Summary")

    bookings_df  = pd.DataFrame(bookings)
    props_lookup = {p["id"]: p["name"] for p in properties}

    if bookings_df.empty:
        st.warning("No bookings yet.")
    else:
        active_bookings = bookings_df[bookings_df["status"] != "cancelled"]

        payout_rows = []
        for _, row in active_bookings.iterrows():
            exp = get_expenses_for_booking(int(row["id"]))
            net, owner_amt, op_amt, platform_amt = compute_split(row["price_total"], exp)
            payout_rows.append({
                "Booking ID": row["id"],
                "Property": props_lookup.get(row["property_id"], f"ID {row['property_id']}"),
                "Guest": row["guest_name"],
                "Check-in": row["check_in"],
                "Check-out": row["check_out"],
                "Nights": row["nights"],
                "Revenue (THB)": row["price_total"],
                "Expenses (THB)": exp,
                "Net (THB)": net,
                f"Owner {OWNER_SHARE*100:.0f}% (THB)": owner_amt,
                f"Operator {OPERATOR_SHARE*100:.0f}% (THB)": op_amt,
                f"Platform {PLATFORM_SHARE*100:.0f}% (THB)": platform_amt,
                "Status": row["status"],
            })
        payout_df = pd.DataFrame(payout_rows)

        # ---- KPI METRICS ----
        total_revenue   = payout_df["Revenue (THB)"].sum()
        total_expenses  = payout_df["Expenses (THB)"].sum()
        total_net       = payout_df["Net (THB)"].sum()
        total_bookings  = len(payout_df)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Revenue",   f"{total_revenue:,.0f} THB")
        k2.metric("Total Expenses",  f"{total_expenses:,.0f} THB")
        k3.metric("Net Profit",      f"{total_net:,.0f} THB")
        k4.metric("Total Bookings",  total_bookings)

        st.markdown("---")

        # ---- ALL-BOOKINGS TABLE ----
        st.markdown("### All Bookings – Payout Breakdown")
        st.dataframe(payout_df, use_container_width=True)

        st.markdown("---")

        # ---- REVENUE BY PROPERTY BAR CHART ----
        st.markdown("### Revenue by Property")
        owner_col = f"Owner {OWNER_SHARE*100:.0f}% (THB)"
        op_col    = f"Operator {OPERATOR_SHARE*100:.0f}% (THB)"
        plat_col  = f"Platform {PLATFORM_SHARE*100:.0f}% (THB)"
        chart_df = (
            payout_df.groupby("Property")[[owner_col, op_col, plat_col]]
            .sum()
            .rename(columns={
                owner_col: f"Owner ({OWNER_SHARE*100:.0f}%)",
                op_col:    f"Operator ({OPERATOR_SHARE*100:.0f}%)",
                plat_col:  f"Platform ({PLATFORM_SHARE*100:.0f}%)",
            })
        )
        st.bar_chart(chart_df)

        st.markdown("---")

        # ---- PER-BOOKING DETAIL & EXPENSE MANAGEMENT ----
        st.markdown("### Per-Booking Detail & Expenses")

        booking_options = {
            row["Booking ID"]: f"#{row['Booking ID']} – {row['Property']} ({row['Guest']})"
            for _, row in payout_df.iterrows()
        }
        selected_bid = st.selectbox(
            "Select booking",
            list(booking_options.keys()),
            format_func=lambda i: booking_options[i],
            key="split_booking"
        )

        sel        = payout_df[payout_df["Booking ID"] == selected_bid].iloc[0]
        exp_total  = sel["Expenses (THB)"]
        net_val    = sel["Net (THB)"]
        owner_val  = sel[f"Owner {OWNER_SHARE*100:.0f}% (THB)"]
        op_val     = sel[f"Operator {OPERATOR_SHARE*100:.0f}% (THB)"]
        plat_val   = sel[f"Platform {PLATFORM_SHARE*100:.0f}% (THB)"]

        d1, d2 = st.columns(2)
        with d1:
            st.write(f"🏡 **{sel['Property']}**")
            st.write(f"👤 Guest: {sel['Guest']}")
            st.write(f"📅 {sel['Check-in']} → {sel['Check-out']} ({sel['Nights']} nights)")
            st.write(f"🔖 Status: **{sel['Status']}**")
        with d2:
            st.metric("Revenue",    f"{sel['Revenue (THB)']:,.0f} THB")
            st.metric("Expenses",   f"{exp_total:,.0f} THB")
            st.metric("Net Profit", f"{net_val:,.0f} THB")

        st.markdown("#### Profit Split")
        s1, s2, s3 = st.columns(3)
        s1.metric(f"👑 Owner ({OWNER_SHARE*100:.0f}%)",      f"{owner_val:,.0f} THB")
        s2.metric(f"🧑‍🔧 Operator ({OPERATOR_SHARE*100:.0f}%)", f"{op_val:,.0f} THB")
        s3.metric(f"🏢 Platform ({PLATFORM_SHARE*100:.0f}%)", f"{plat_val:,.0f} THB")

        expense_rows = [e for e in expenses if e["booking_id"] == selected_bid]
        with st.expander(f"Expense breakdown ({len(expense_rows)} items, total {exp_total:,.0f} THB)"):
            if expense_rows:
                st.dataframe(pd.DataFrame(expense_rows)[["description", "amount"]], use_container_width=True)
            else:
                st.caption("No expenses recorded for this booking.")

            st.markdown("**Add expense**")
            ec1, ec2, ec3 = st.columns([3, 2, 1])
            with ec1:
                exp_desc = st.text_input("Description", key="exp_desc")
            with ec2:
                exp_amt = st.number_input("Amount (THB)", min_value=0.0, step=100.0, key="exp_amt")
            with ec3:
                st.write("")
                st.write("")
                if st.button("Add", key="add_expense_btn"):
                    if exp_desc.strip() and exp_amt > 0:
                        db.add_expense(int(selected_bid), exp_desc.strip(), float(exp_amt))
                        st.rerun()
                    else:
                        st.warning("Enter description and amount.")

        st.markdown("---")

    # ---- OWNER & OPERATOR TOTALS ----
    st.markdown("### Owner Totals")
    owners = [u for u in users if u["role"] == "owner"]
    owner_rows = [
        {"Name": o["name"], "Bookings": ob, "Earnings (THB)": round(oe, 2)}
        for o in owners
        for ob, oe in [summarize_for_owner(o["id"])]
    ]
    if owner_rows:
        st.dataframe(pd.DataFrame(owner_rows), use_container_width=True)

    st.markdown("### Operator Totals")
    operators = [u for u in users if u["role"] == "operator"]
    op_rows = [
        {"Name": o["name"], "Bookings": ob, "Earnings (THB)": round(oe, 2)}
        for o in operators
        for ob, oe in [summarize_for_operator(o["id"])]
    ]
    if op_rows:
        st.dataframe(pd.DataFrame(op_rows), use_container_width=True)
