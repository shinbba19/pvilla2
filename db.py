from datetime import date

import streamlit as st
from supabase import create_client


@st.cache_resource
def get_client():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


# ---------- USERS ----------

def get_users() -> list[dict]:
    return get_client().table("users").select("*").order("id").execute().data


def add_user(name: str, role: str) -> int:
    row = get_client().table("users").insert({"name": name, "role": role}).execute().data[0]
    return row["id"]


# ---------- PROPERTIES ----------

def get_properties() -> list[dict]:
    return get_client().table("properties").select("*").order("id").execute().data


def add_property(
    name: str,
    location: str,
    owner_id: int,
    operator_id: int,
    nightly_rate: float,
    image_url: str = "https://images.pexels.com/photos/261102/pexels-photo-261102.jpeg",
    description: str = "Newly added pool villa by owner.",
    bedrooms: int = 3,
    baths: int = 3,
    guests: int = 6,
) -> int:
    row = get_client().table("properties").insert({
        "name": name,
        "location": location,
        "owner_id": owner_id,
        "operator_id": operator_id,
        "nightly_rate": nightly_rate,
        "image_url": image_url,
        "description": description,
        "bedrooms": bedrooms,
        "baths": baths,
        "guests": guests,
        "rating": 5.0,
        "reviews": 0,
        "cleaning_status": "needs_cleaning",
    }).execute().data[0]
    return row["id"]


def set_cleaning_status(property_id: int, status: str):
    get_client().table("properties").update({"cleaning_status": status}).eq("id", property_id).execute()


def update_property_image(property_id: int, image_url: str):
    get_client().table("properties").update({"image_url": image_url}).eq("id", property_id).execute()


# ---------- BOOKINGS ----------

def get_bookings() -> list[dict]:
    rows = get_client().table("bookings").select("*").order("id").execute().data
    # Convert date strings to date objects
    for r in rows:
        if isinstance(r["check_in"], str):
            r["check_in"] = date.fromisoformat(r["check_in"])
        if isinstance(r["check_out"], str):
            r["check_out"] = date.fromisoformat(r["check_out"])
    return rows


def add_booking(
    property_id: int,
    guest_name: str,
    check_in: date,
    check_out: date,
    nights: int,
    price_total: float,
) -> int:
    row = get_client().table("bookings").insert({
        "property_id": property_id,
        "guest_name": guest_name,
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "nights": nights,
        "price_total": price_total,
        "status": "booked",
    }).execute().data[0]
    return row["id"]


def update_booking_status(booking_id: int, status: str):
    get_client().table("bookings").update({"status": status}).eq("id", booking_id).execute()


# ---------- EXPENSES ----------

def get_expenses() -> list[dict]:
    return get_client().table("expenses").select("*").order("id").execute().data


def add_expense(booking_id: int, description: str, amount: float) -> int:
    row = get_client().table("expenses").insert({
        "booking_id": booking_id,
        "description": description,
        "amount": amount,
    }).execute().data[0]
    return row["id"]


def get_expenses_for_booking(booking_id: int) -> float:
    rows = get_client().table("expenses").select("amount").eq("booking_id", booking_id).execute().data
    return float(sum(r["amount"] for r in rows))


# ---------- IMAGE UPLOAD (Supabase Storage) ----------

def upload_property_image(property_id: int, image_bytes: bytes, content_type: str = "image/jpeg") -> str:
    """Upload image to Supabase Storage and return public URL."""
    client = get_client()
    bucket = "property-images"
    path = f"{property_id}/{property_id}_main.jpg"
    client.storage.from_(bucket).upload(
        path, image_bytes, {"content-type": content_type, "upsert": "true"}
    )
    return client.storage.from_(bucket).get_public_url(path)
