# test_fetch_wells_ops.py
import asyncio
from well_client.fetch_api import fetch_wells_ops_list

async def main():
    wells_ops = await fetch_wells_ops_list()
    print(f"Fetched {len(wells_ops)} wells with status OPS:\n")
    for idx, well in enumerate(wells_ops, start=1):
        print(f"--- Well OPS #{idx} ---")
        for k, v in well.items():
            print(f"{k}: {v}")
        print("-------------------\n")

if __name__ == "__main__":
    asyncio.run(main())