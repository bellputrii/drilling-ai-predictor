# test_fetch_well_realtime.py
import asyncio
from well_client.fetch_api import fetch_well_realtime

# Ganti sesuai token sumur yang ingin diuji
TOKEN = "ea1210d9edd8f1d87258d809b4ba477c"
START_TIME = "2026-05-30 14:34:00"
END_TIME = "2026-05-30 14:39:00"

async def main():
    try:
        records = await fetch_well_realtime(TOKEN, START_TIME, END_TIME)
        if not records:
            print("No well data found.")
            return
        print(f"Fetched {len(records)} records for well token {TOKEN}:\n")
        for idx, rec in enumerate(records, 1):
            print(f"--- Record #{idx} ---")
            for k, v in rec.items():
                print(f"{k}: {v}")
            print("----------------------\n")
    except Exception as e:
        print("Error fetching well data:", e)

if __name__ == "__main__":
    asyncio.run(main())