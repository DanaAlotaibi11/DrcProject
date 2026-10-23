import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Supabase URL or key is missing from the .env file")

supabase = create_client(url, key)

response = (
    supabase.table("sensor_readings")
    .select("*")
    .order("created_at", desc=True)
    .limit(1)
    .execute()
)

if response.data:
    latest = response.data[0]

    print("Latest VibraFlow reading:")
    print("Device:", latest["device_id"])
    print("Microphone 1:", latest["mic1"])
    print("Microphone 2:", latest["mic2"])
    print("Microphone 3:", latest["mic3"])
    print("Microphone 4:", latest["mic4"])
    print("Vibration:", latest["vibration"])
    print("Status:", latest["status"])
    print("Time:", latest["created_at"])
else:
    print("No sensor readings found.")