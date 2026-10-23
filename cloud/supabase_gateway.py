import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

if not URL or not KEY:
    raise ValueError("Supabase credentials are missing from .env")

supabase = create_client(URL, KEY)


def upload_reading(
    mic1=None,
    mic2=None,
    mic3=None,
    mic4=None,
    vibration=None,
    status="Waiting",
    device_id="VibraFlow-01"
):
    valid_statuses = {"Waiting", "Normal", "Potential Leak"}

    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}")

    reading = {
        "device_id": device_id,
        "mic1": mic1,
        "mic2": mic2,
        "mic3": mic3,
        "mic4": mic4,
        "vibration": vibration,
        "status": status
    }

    response = (
        supabase.table("sensor_readings")
        .insert(reading)
        .execute()
    )

    return response.data


def get_latest_reading():
    response = (
        supabase.table("sensor_readings")
        .select("*")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    return response.data[0] if response.data else None