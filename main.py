import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="StayOps Prototype", layout="wide")

# ----------------- CONFIG -----------------
OWNER_SHARE = 0.65
OPERATOR_SHARE = 0.25
PLATFORM_SHARE = 0.10

# ----------------- INIT MOCK DATA -----------------
def init_mock():
    # Users
    st.session_state.users = [
        {"id": 1, "name": "Alice (Owner)", "role": "owner"},
        {"id": 2, "name": "Bob (Operator)", "role": "operator"},
        {"id": 3, "name": "Charlie (Guest)", "role": "guest"},
    ]

    # Properties – MORE MOCK LISTINGS
    st.session_state.properties = [
        {
            "id": 1,
            "name": "Khaoyai Sunset Villa",
            "location": "Khao Yai, Thailand",
            "owner_id": 1,
            "operator_id": 2,
            "nightly_rate": 6000.0,
            "rating": 4.8,
            "reviews": 32,
            "bedrooms": 3,
            "baths": 3,
            "guests": 6,
            "image_url": "https://images.pexels.com/photos/261102/pexels-photo-261102.jpeg",
            "description": "Private pool villa with mountain view, perfect for wellness & pet-friendly stays.",
            "cleaning_status": "needs_cleaning",
        },
        {
            "id": 2,
            "name": "Forest Retreat Pool Villa",
            "location": "Khao Yai, Thailand",
            "owner_id": 1,
            "operator_id": 2,
            "nightly_rate": 7500.0,
            "rating": 4.9,
            "reviews": 18,
            "bedrooms": 4,
            "baths": 4,
            "guests": 8,
            "image_url": "https://images.pexels.com/photos/32870/pexels-photo.jpg",
            "description": "Surrounded by trees, ideal for yoga retreats and quiet escapes from Bangkok.",
            "cleaning_status": "needs_cleaning",
        },
        {
            "id": 3,
            "name": "Skyline Mountain View Villa",
            "location": "Khao Yai, Thailand",
            "owner_id": 1,
            "operator_id": 2,
            "nightly_rate": 9000.0,
            "rating": 4.7,
            "reviews": 24,
            "bedrooms": 5,
            "baths": 5,
            "guests": 10,
            "image_url": "https://images.pexels.com/photos/258154/pexels-photo-258154.jpeg",
            "description": "Spacious villa with panoramic mountain views, great for large groups & events.",
            "cleaning_status": "needs_cleaning",
        },
        {
            "id": 4,
            "name": "Minimal Zen Pool House",
            "location": "Khao Yai, Thailand",
            "owner_id": 1,
            "operator_id": 2,
            "nightly_rate": 5500.0,
            "rating": 4.6,
            "reviews": 15,
            "bedrooms": 2,
            "baths": 2,
            "guests": 4,
            "image_url": "https://images.pexels.com/photos/1571460/pexels-photo-1571460.jpeg",
            "description": "Calm, minimal villa with private pool, ideal for couples and small families.",
            "cleaning_status": "needs_cleaning",
        },
        {
            "id": 5,
            "name": "Family Garden Pool Villa",
            "location": "Khao Yai, Thailand",
            "owner_id": 1,
            "operator_id": 2,
            "nightly_rate": 6800.0,
            "rating": 4.5,
            "reviews": 21,
            "bedrooms": 3,
            "baths": 3,
            "guests": 7,
            "image_url": "https://images.pexels.com/photos/261187/pexels-photo-261187.jpeg",
            "description": "Lush garden, BBQ area and kids-friendly pool – perfect for family trips.",
            "cleaning_status": "needs_cleaning",
        },
        {
            "id": 6,
            "name": "Wellness Retreat Pool Villa",
            "location": "Khao Yai, Thailand",
            "owner_id": 1,
            "operator_id": 2,
            "nightly_rate": 8200.0,
            "rating": 5.0,
            "reviews": 11,
            "bedrooms": 4,
            "baths": 4,
            "guests": 8,
            "image_url": "https://images.pexels.com/photos/1458457/pexels-photo-1458457.jpeg",
            "description": "Designed for wellness: yoga deck, quiet surroundings and detox-friendly kitchen.",
            "cleaning_status": "needs_cleaning",
        },
    ]

    # Bookings – still one initial booking as example
    st.session_state.bookings = [
        {
            "id": 1,
            "property_id": 1,
            "guest_name": "Charlie (Guest)",
            "check_in": date(2025, 1, 10),
            "check_out": date(2025, 1, 12),
            "nights": 2,
            "price_total": 12000.0,
            "status": "completed",
        }
    ]

    # Expenses
    st.session_state.expenses = [
        {"id": 1, "booking_id": 1, "description": "Cleaning", "amount": 500.0},
        {"id": 2, "booking_id": 1, "description": "Minor Repair", "amount": 300.0},
    ]

    # UI state
    st.session_state.selected_property_id = None
    st.session_state.pending_payment_booking_id = None
    st.session_state.property_images = {}  # prop_id -> bytes
    st.session_state.payment_just_completed = False

if "initialized" not in st.session_state:
    st.session_state.initialized = True
    init_mock()

# ----------------- HELPERS -----------------
def get_new_id(items):
    if not items:
        return 1
    return max(i["id"] for i in items) + 1

def add_user(name: str, role: str):
    new_id = get_new_id(st.session_state.users)
    st.session_state.users.append({"id": new_id, "name": name, "role": role})
    return new_id

DEFAULT_IMAGE = "https://images.pexels.com/photos/261102/pexels-photo-261102.jpeg"

def add_property(name: str, location: str, owner_id: int, operator_id: int, nightly_rate: float, image_url: str = DEFAULT_IMAGE):
    new_id = get_new_id(st.session_state.properties)
    st.session_state.properties.append(
        {
            "id": new_id,
            "name": name,
            "location": location,
            "owner_id": owner_id,
            "operator_id": operator_id,
            "nightly_rate": nightly_rate,
            "rating": 5.0,
            "reviews": 0,
            "bedrooms": 3,
            "baths": 3,
            "guests": 6,
            "image_url": image_url,
            "description": "Newly added pool villa by owner.",
            "cleaning_status": "needs_cleaning",
        }
    )
    return new_id

def add_booking(property_id: int, guest_name: str, check_in: date, check_out: date, nights: int) -> int:
    prop = next(p for p in st.session_state.properties if p["id"] == property_id)
    price_total = prop["nightly_rate"] * nights
    new_id = get_new_id(st.session_state.bookings)
    st.session_state.bookings.append(
        {
            "id": new_id,
            "property_id": property_id,
            "guest_name": guest_name,
            "check_in": check_in,
            "check_out": check_out,
            "nights": nights,
            "price_total": price_total,
            "status": "booked",
        }
    )
    return new_id

def add_expense(booking_id: int, desc: str, amount: float):
    new_id = get_new_id(st.session_state.expenses)
    st.session_state.expenses.append(
        {"id": new_id, "booking_id": booking_id, "description": desc, "amount": amount}
    )

def get_expenses_for_booking(booking_id: int) -> float:
    df = pd.DataFrame(st.session_state.expenses)
    if df.empty:
        return 0.0
    return float(df[df["booking_id"] == booking_id]["amount"].sum())

def get_property_image(prop_id: int, image_url: str):
    """Returns first uploaded image bytes, or the fallback URL."""
    imgs = st.session_state.get("property_images", {}).get(prop_id)
    return imgs[0] if imgs else image_url

def get_all_property_images(prop_id: int, image_url: str):
    """Returns list of all uploaded image bytes, or [fallback_url]."""
    imgs = st.session_state.get("property_images", {}).get(prop_id)
    return imgs if imgs else [image_url]

def has_conflict(property_id: int, check_in: date, check_out: date) -> bool:
    for b in st.session_state.bookings:
        if b["property_id"] != property_id:
            continue
        if b.get("status") == "cancelled":
            continue
        if check_in < b["check_out"] and check_out > b["check_in"]:
            return True
    return False

def compute_split(price_total: float, expenses: float):
    net = max(price_total - expenses, 0.0)
    owner_amt = net * OWNER_SHARE
    operator_amt = net * OPERATOR_SHARE
    platform_amt = net * PLATFORM_SHARE
    return net, owner_amt, operator_amt, platform_amt

def summarize_for_owner(owner_id: int):
    props = [p["id"] for p in st.session_state.properties if p["owner_id"] == owner_id]
    if not props:
        return 0, 0.0
    total_bookings = 0
    total_owner = 0.0
    for b in st.session_state.bookings:
        if b["property_id"] in props:
            expenses = get_expenses_for_booking(b["id"])
            _, owner_amt, _, _ = compute_split(b["price_total"], expenses)
            total_bookings += 1
            total_owner += owner_amt
    return total_bookings, total_owner

def summarize_for_operator(operator_id: int):
    props = [p["id"] for p in st.session_state.properties if p["operator_id"] == operator_id]
    if not props:
        return 0, 0.0
    total_bookings = 0
    total_op = 0.0
    for b in st.session_state.bookings:
        if b["property_id"] in props:
            expenses = get_expenses_for_booking(b["id"])
            _, _, op_amt, _ = compute_split(b["price_total"], expenses)
            total_bookings += 1
            total_op += op_amt
    return total_bookings, total_op

# ----------------- UI LAYOUT -----------------
st.title("StayOps – Pool Villa Platform Prototype")
st.caption("Owner ↔ Operator ↔ Guest with date-based booking & profit sharing (mock)")

tab_guest, tab_owner, tab_operator, tab_payout = st.tabs(
    ["🏡 Guest (Airbnb-style)", "👑 Owner", "🧑‍🔧 Operator", "💰 Payout Summary"]
)

# ---------- TAB 1: GUEST (AIRBNB-LIKE PAGE) ----------
with tab_guest:
    if st.session_state.get("payment_just_completed"):
        # ---- PAYMENT SUCCESS VIEW ----
        st.markdown("## ✅ Payment Successful!")
        st.success("Your booking has been confirmed. Thank you for your reservation!")
        st.balloons()
        if st.button("← Back to main page", key="back_after_payment"):
            st.session_state.payment_just_completed = False
            st.rerun()

    elif st.session_state.pending_payment_booking_id is not None:
        # ---- PAYMENT VIEW ----
        pay_bid = st.session_state.pending_payment_booking_id
        pay_booking = next(b for b in st.session_state.bookings if b["id"] == pay_bid)
        pay_prop = next(p for p in st.session_state.properties if p["id"] == pay_booking["property_id"])

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
            card_name = st.text_input("Cardholder name", key="pay_card_name")
            card_number = st.text_input("Card number", placeholder="•••• •••• •••• ••••", max_chars=19, key="pay_card_number")
            card_expiry = st.text_input("Expiry (MM/YY)", max_chars=5, key="pay_expiry")
            card_cvv = st.text_input("CVV", max_chars=4, key="pay_cvv")

            if st.button(f"Pay {pay_booking['price_total']:.0f} THB", key="pay_now"):
                digits = card_number.replace(" ", "").replace("-", "")
                if not all([card_name.strip(), card_number.strip(), card_expiry.strip(), card_cvv.strip()]):
                    st.error("Please fill in all card details.")
                elif not digits.isdigit() or not (13 <= len(digits) <= 19):
                    st.error("Please enter a valid card number.")
                else:
                    for b in st.session_state.bookings:
                        if b["id"] == pay_bid:
                            b["status"] = "paid"
                            break
                    st.session_state.pending_payment_booking_id = None
                    st.session_state.payment_just_completed = True
                    st.rerun()

            if st.button("Cancel payment", key="pay_cancel"):
                st.session_state.pending_payment_booking_id = None
                st.rerun()

    elif st.session_state.selected_property_id is not None:
        # ---- DETAIL VIEW ----
        prop = next(p for p in st.session_state.properties if p["id"] == st.session_state.selected_property_id)

        if st.button("← Back to listings"):
            st.session_state.selected_property_id = None
            st.rerun()

        st.markdown("## Selected stay")
        left, right = st.columns([2, 1])

        with left:
            for img in get_all_property_images(prop["id"], prop["image_url"]):
                st.image(img, use_column_width=True)
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
            check_in = st.date_input("Check-in date", value=date.today(), key="detail_check_in")
            check_out = st.date_input("Check-out date", value=date.today(), key="detail_check_out")
            guest_name = st.text_input("Guest name", value="Demo Guest", key="detail_guest_name")
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
                    st.error("These dates are already booked for this property. Please choose different dates.")
                else:
                    bid = add_booking(prop["id"], guest_name, check_in, check_out, nights)
                    st.session_state.selected_property_id = None
                    st.session_state.pending_payment_booking_id = bid
                    st.rerun()

    else:
        # ---- LISTINGS VIEW ----
        st.subheader("Find your wellness & pet-friendly pool villa in Khao Yai")

        with st.container():
            col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 1])
            with col_a:
                search_location = st.text_input("Location", value="Khao Yai", key="search_location")
            with col_b:
                search_check_in = st.date_input("Check in", value=date.today(), key="search_check_in")
            with col_c:
                search_check_out = st.date_input("Check out", value=date.today(), key="search_check_out")
            with col_d:
                search_guests = st.number_input("Guests", min_value=1, max_value=16, value=1, key="search_guests")

        st.markdown("---")
        st.markdown("### Stays in Khao Yai")

        props_df = pd.DataFrame(st.session_state.properties)
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
                    st.image(get_property_image(int(row["id"]), row["image_url"]), use_column_width=True)
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

    users_df = pd.DataFrame(st.session_state.users)
    owners_df = users_df[users_df["role"] == "owner"]
    operators_df = users_df[users_df["role"] == "operator"]

    st.markdown("### Existing Owners")
    st.dataframe(owners_df)

    st.markdown("### Add new owner")
    new_owner_name = st.text_input("New owner name")
    if st.button("Create owner"):
        if new_owner_name.strip():
            oid = add_user(new_owner_name.strip(), "owner")
            st.success(f"Owner created with ID: {oid}")
        else:
            st.warning("Please enter a name.")

    st.markdown("---")
    st.markdown("### Add new pool villa")

    if owners_df.empty or operators_df.empty:
        st.info("Need at least 1 owner and 1 operator to add a property.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            pname = st.text_input("Property name", value="New Khao Yai Pool Villa")
            ploc = st.text_input("Location", value="Khao Yai, Thailand")
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
        img_bytes = None
        _slot = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"], key="villa_img_1")
        if _slot is not None:
            img_bytes = _slot.read()
            st.image(img_bytes, width=160)

        if st.button("Add pool villa"):
            pid = add_property(pname, ploc, int(owner_id), int(operator_id), float(nightly_rate))
            if img_bytes:
                st.session_state.property_images[pid] = [img_bytes]
            st.success(f"🏡 New property created with ID: {pid}")
            st.rerun()

    st.markdown("### All properties")
    st.dataframe(pd.DataFrame(st.session_state.properties))

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
        owner_prop_ids = [
            p["id"] for p in st.session_state.properties
            if p["owner_id"] == selected_owner_id
        ]
        bookings_df = pd.DataFrame(st.session_state.bookings)
        if not bookings_df.empty and owner_prop_ids:
            owner_bookings = bookings_df[bookings_df["property_id"].isin(owner_prop_ids)].copy()
            if owner_bookings.empty:
                st.info("No bookings for this owner's properties yet.")
            else:
                props_lookup = {p["id"]: p["name"] for p in st.session_state.properties}
                owner_bookings["property_name"] = owner_bookings["property_id"].map(props_lookup)
                st.dataframe(
                    owner_bookings[["id", "property_name", "guest_name", "check_in", "check_out", "nights", "price_total", "status"]]
                )
        else:
            st.info("No bookings for this owner's properties yet.")

# ---------- TAB 3: OPERATOR ----------
with tab_operator:
    st.subheader("Housekeeper Dashboard")

    users_df = pd.DataFrame(st.session_state.users)
    operators_df = users_df[users_df["role"] == "operator"]

    if operators_df.empty:
        st.info("No housekeepers registered yet.")
    else:
        op_id = st.selectbox(
            "Who are you?",
            operators_df["id"],
            format_func=lambda i: operators_df[operators_df.id == i]["name"].iloc[0],
            key="hk_select"
        )

        assigned_props = [p for p in st.session_state.properties if p["operator_id"] == op_id]

        st.markdown("### Your assigned properties")

        if not assigned_props:
            st.info("You have no properties assigned to you yet.")
        else:
            for prop in assigned_props:
                col1, col2, col3 = st.columns([3, 1.5, 1.5])
                with col1:
                    st.markdown(f"**{prop['name']}**")
                    st.caption(prop["location"])
                with col2:
                    if prop["cleaning_status"] == "clean":
                        st.success("🟢 Clean")
                    else:
                        st.error("🔴 Needs Cleaning")
                with col3:
                    if prop["cleaning_status"] == "clean":
                        if st.button("Mark as Needs Cleaning", key=f"hk_toggle_{prop['id']}"):
                            for p in st.session_state.properties:
                                if p["id"] == prop["id"]:
                                    p["cleaning_status"] = "needs_cleaning"
                                    break
                            st.rerun()
                    else:
                        if st.button("Mark as Clean", key=f"hk_toggle_{prop['id']}"):
                            for p in st.session_state.properties:
                                if p["id"] == prop["id"]:
                                    p["cleaning_status"] = "clean"
                                    break
                            st.rerun()
                st.markdown("---")

    st.markdown("### Add new housekeeper")
    new_operator_name = st.text_input("New housekeeper name")
    if st.button("Create housekeeper"):
        if new_operator_name.strip():
            oid = add_user(new_operator_name.strip(), "operator")
            st.success(f"Housekeeper created with ID: {oid}")
        else:
            st.warning("Please enter a name.")

# ---------- TAB 4: PAYOUT SUMMARY ----------
with tab_payout:
    st.subheader("Per booking profit split")

    bookings_df = pd.DataFrame(st.session_state.bookings)
    if bookings_df.empty:
        st.warning("No bookings yet.")
    else:
        booking_id = st.selectbox("Select booking", bookings_df["id"], key="split_booking")
        b = bookings_df[bookings_df.id == booking_id].iloc[0]
        expenses_total = get_expenses_for_booking(int(booking_id))
        net, owner_amt, op_amt, platform_amt = compute_split(b["price_total"], expenses_total)

        st.write(f"🏡 Property ID: {b['property_id']}")
        st.write(f"👤 Guest: {b['guest_name']}")
        st.write(f"📅 {b['check_in']} → {b['check_out']} ({b['nights']} nights)")
        st.write(f"💰 Price Total: **{b['price_total']:.2f} THB**")
        st.write(f"🧾 Total Expenses: **{expenses_total:.2f} THB**")
        st.write(f"🏦 Net Profit: **{net:.2f} THB**")

        st.markdown("### Split")
        st.success(
            f"- 👑 Owner ({OWNER_SHARE*100:.0f}%): **{owner_amt:.2f} THB**\n"
            f"- 🧑‍🔧 Operator ({OPERATOR_SHARE*100:.0f}%): **{op_amt:.2f} THB**\n"
            f"- 🏢 Platform ({PLATFORM_SHARE*100:.0f}%): **{platform_amt:.2f} THB**"
        )

    st.markdown("---")
    st.subheader("Owner & Operator totals (mock)")

    owners = [u for u in st.session_state.users if u["role"] == "owner"]
    operators = [u for u in st.session_state.users if u["role"] == "operator"]

    for owner in owners:
        ob, oe = summarize_for_owner(owner["id"])
        st.info(f"👑 {owner['name']} → Bookings: {ob}, Estimated Earnings: {oe:.2f} THB")

    for op in operators:
        ob2, oe2 = summarize_for_operator(op["id"])
        st.info(f"🧑‍🔧 {op['name']} → Bookings: {ob2}, Estimated Earnings: {oe2:.2f} THB")
