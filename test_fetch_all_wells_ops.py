# test_fetch_all_wells_ops.py
import asyncio
from well_client.fetch_api import fetch_all_wells_ops_realtime

# Bisa diberikan start_time dan end_time manual, jika None maka ambil default 1 jam terakhir
START_TIME = None
END_TIME = None

async def main():
    try:
        records = await fetch_all_wells_ops_realtime(start_time=START_TIME, end_time=END_TIME)
        if not records:
            print("No OPS wells data found.")
            return
        print(f"Fetched {len(records)} records for all OPS wells:\n")
        for idx, rec in enumerate(records, 1):
            print(f"--- Record #{idx} | Well: {rec.get('well_name')} ---")
            for k, v in rec.items():
                print(f"{k}: {v}")
            print("----------------------\n")
    except Exception as e:
        print("Error fetching all OPS wells data:", e)

if __name__ == "__main__":
    asyncio.run(main())