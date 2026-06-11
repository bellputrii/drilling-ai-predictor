import argparse
import csv
import http.client
import json
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


REALTIME_DATA_HOST = "pdumitradome.id"
REALTIME_DATA_PATH = "/dome_api/realtime-data"
WELLS_ACTIVE_PATH = "/dome_api/wells-active"

DEFAULT_PARAM = [
    "dt",
    "md",
    "bitdepth",
    "blockpos",
    "hklda",
    "mudflowin",
    "ropi",
    "rpm",
    "torqa",
    "stppress",
    "woba",
    "speedup",
    "speeddown",
]


def request_json(
    method: str,
    path: str,
    payload: Optional[dict] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Helper request HTTP menggunakan standard library.
    API realtime-data memakai GET dengan JSON body, jadi payload tetap dikirim.
    """
    body = json.dumps(payload) if payload is not None else ""
    headers = {"Content-Type": "application/json"} if payload is not None else {}

    conn = http.client.HTTPSConnection(REALTIME_DATA_HOST, timeout=timeout)

    try:
        conn.request(method, path, body, headers)
        res = conn.getresponse()
        raw = res.read().decode("utf-8", errors="replace")

        if res.status != 200:
            raise RuntimeError(f"API failed: {res.status} {res.reason} | response={raw[:500]}")

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Response bukan JSON valid: {raw[:500]}") from exc

    finally:
        conn.close()


async def fetch_wells_active() -> List[Dict[str, Any]]:
    """Ambil semua wells."""
    response = await asyncio.to_thread(
        request_json,
        "GET",
        WELLS_ACTIVE_PATH,
        None,
    )
    return response.get("result", []) or []


async def fetch_wells_ops_list() -> List[Dict[str, Any]]:
    """Filter wells dengan status OPS."""
    wells = await fetch_wells_active()
    return [well for well in wells if well.get("well_status") == "OPS"]


async def fetch_well_realtime(
    token: str,
    start_time: str,
    end_time: str,
    param: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Ambil data realtime per well."""
    if param is None:
        param = DEFAULT_PARAM

    payload = {
        "token": token,
        "timeStart": start_time,
        "timeEnd": end_time,
        "param": param,
    }

    response = await asyncio.to_thread(
        request_json,
        "GET",
        REALTIME_DATA_PATH,
        payload,
    )
    return response.get("result", []) or []


async def fetch_all_wells_ops_realtime(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    param: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Ambil semua realtime data dari well yang statusnya OPS.

    Return:
    {
        "start_time": "...",
        "end_time": "...",
        "total_wells_ops": 0,
        "total_records": 0,
        "summary_per_well": [...],
        "errors": [...],
        "data": [...]
    }
    """
    if param is None:
        param = DEFAULT_PARAM

    now = datetime.utcnow()

    if not end_time:
        end_time = now.strftime("%Y-%m-%d %H:%M:%S")

    if not start_time:
        start_time = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

    wells_ops = await fetch_wells_ops_list()

    all_data: List[Dict[str, Any]] = []
    summary_per_well: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for idx, well in enumerate(wells_ops, start=1):
        wid = well.get("wid")
        well_name = well.get("well_name")
        token = well.get("is_api_token")

        print(f"[{idx}/{len(wells_ops)}] Fetch well OPS: {well_name} | wid={wid}")

        if not token:
            error_item = {
                "wid": wid,
                "well_name": well_name,
                "error": "Token kosong / is_api_token tidak tersedia",
            }
            errors.append(error_item)
            print(f"  -> SKIP: {error_item['error']}")
            continue

        try:
            well_data = await fetch_well_realtime(
                token=token,
                start_time=start_time,
                end_time=end_time,
                param=param,
            )

            for record in well_data:
                record["wid"] = wid
                record["well_name"] = well_name

            all_data.extend(well_data)

            summary_item = {
                "wid": wid,
                "well_name": well_name,
                "records": len(well_data),
            }
            summary_per_well.append(summary_item)

            print(f"  -> OK: {len(well_data)} records")

        except Exception as exc:
            error_item = {
                "wid": wid,
                "well_name": well_name,
                "error": str(exc),
            }
            errors.append(error_item)
            print(f"  -> ERROR: {exc}")

    return {
        "start_time": start_time,
        "end_time": end_time,
        "total_wells_ops": len(wells_ops),
        "total_records": len(all_data),
        "summary_per_well": summary_per_well,
        "errors": errors,
        "data": all_data,
    }


def save_json(path: str, result: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)


def save_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        print(f"CSV tidak dibuat karena data kosong: {path}")
        return

    fieldnames = sorted({key for row in rows for key in row.keys()})

    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_preview(rows: List[Dict[str, Any]], limit: int = 5) -> None:
    print("\n=== Preview Data ===")
    if not rows:
        print("Data kosong.")
        return

    for i, row in enumerate(rows[:limit], start=1):
        print(f"\nData #{i}")
        print(json.dumps(row, indent=2, ensure_ascii=False))


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test fetch semua realtime data dari well berstatus OPS."
    )

    parser.add_argument(
        "--hours",
        type=float,
        default=1,
        help="Range waktu mundur dari sekarang dalam jam. Default: 1 jam.",
    )
    parser.add_argument(
        "--start-time",
        type=str,
        default=None,
        help='Start time format: "YYYY-MM-DD HH:MM:SS". Jika diisi, --hours diabaikan.',
    )
    parser.add_argument(
        "--end-time",
        type=str,
        default=None,
        help='End time format: "YYYY-MM-DD HH:MM:SS". Default: waktu UTC sekarang.',
    )
    parser.add_argument(
        "--json",
        type=str,
        default="realtime_ops_result.json",
        help="Path output JSON. Default: realtime_ops_result.json",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Path output CSV. Contoh: realtime_ops_result.csv",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=5,
        help="Jumlah data preview di terminal. Default: 5",
    )

    args = parser.parse_args()

    end_time = args.end_time
    start_time = args.start_time

    if not end_time:
        end_dt = datetime.utcnow()
        end_time = end_dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

    if not start_time:
        start_dt = end_dt - timedelta(hours=args.hours)
        start_time = start_dt.strftime("%Y-%m-%d %H:%M:%S")

    print("=== TEST FETCH ALL WELLS OPS REALTIME ===")
    print(f"Host       : {REALTIME_DATA_HOST}")
    print(f"Start Time : {start_time}")
    print(f"End Time   : {end_time}")
    print(f"Param      : {DEFAULT_PARAM}")
    print("=========================================\n")

    result = await fetch_all_wells_ops_realtime(
        start_time=start_time,
        end_time=end_time,
        param=DEFAULT_PARAM,
    )

    print("\n=== Summary ===")
    print(f"Total wells OPS : {result['total_wells_ops']}")
    print(f"Total records   : {result['total_records']}")
    print(f"Total errors    : {len(result['errors'])}")

    print("\n=== Summary Per Well ===")
    for item in result["summary_per_well"]:
        print(f"- {item['well_name']} | wid={item['wid']} | records={item['records']}")

    if result["errors"]:
        print("\n=== Errors ===")
        for err in result["errors"]:
            print(f"- {err['well_name']} | wid={err['wid']} | error={err['error']}")

    print_preview(result["data"], limit=args.preview)

    save_json(args.json, result)
    print(f"\nJSON saved to: {args.json}")

    if args.csv:
        save_csv(args.csv, result["data"])
        print(f"CSV saved to : {args.csv}")


if __name__ == "__main__":
    asyncio.run(main())
