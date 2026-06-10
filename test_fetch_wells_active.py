# test_fetch_wells_active.py
import asyncio
from well_client.fetch_api import fetch_wells_active, fetch_wells_ops_list

async def main():
    # Ambil semua wells aktif
    all_wells = await fetch_wells_active()
    print(f"Total wells: {len(all_wells)}")
    for w in all_wells:
        print(f"{w['wid']} | {w['well_name']} | Status: {w.get('well_status')}")

    print("\n--- Wells OPS Only ---")
    ops_wells = await fetch_wells_ops_list()
    for w in ops_wells:
        print(f"{w['wid']} | {w['well_name']} | Status: {w.get('well_status')}")

if __name__ == "__main__":
    asyncio.run(main())