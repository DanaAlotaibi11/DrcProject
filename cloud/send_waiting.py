import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Supabase URL or key is missing from the .env file")

supabase = create_client(url, key)

reading = {
    "device_id": "VibraFlow-01",
    "mic1": None,
    "mic2": None,
    "mic3": None,
    "mic4": None,
    "vibration": None,
    "status": "Waiting"
}

response = supabase.table("sensor_readings").insert(reading).execute()

print("Successfully connected to Supabase.")
print("Waiting record added:", response.data)