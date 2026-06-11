import http.client
import json
from datetime import datetime, timedelta

REALTIME_DATA_HOST = "pdumitradome.id"
REALTIME_DATA_PATH = "/dome_api/realtime-data"
WELLS_ACTIVE_PATH = "/dome_api/wells-active"

DEFAULT_PARAM = [
    "dt", "md", "bitdepth", "blockpos", "hklda", "mudflowin",
    "ropi", "rpm", "torqa", "stppress", "woba", "speedup", "speeddown", "md"
]


def is_no_data_time_range_error(error_message: str) -> bool:
    """
    Deteksi error API ketika tidak ada data pada range waktu tertentu.
    Contoh:
    404 Not Found | response={"status":404,"message":"No data found for the given time range"}
    """
    message = str(error_message).lower()
    return (
        "404" in message
        and (
            "no data found for the given time range" in message
            or "no data" in message
            or "not found" in message
        )
    )


async def fetch_wells_active() -> list:
    """Ambil semua wells"""
    conn = http.client.HTTPSConnection(REALTIME_DATA_HOST)
    try:
        conn.request("GET", WELLS_ACTIVE_PATH, "", {})
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode()).get("result", [])
    finally:
        conn.close()


async def fetch_wells_ops_list() -> list:
    """Filter wells dengan status OPS"""
    wells = await fetch_wells_active()
    return [well for well in wells if well.get("well_status") == "OPS"]


async def fetch_well_realtime(token: str, start_time: str, end_time: str, param=None) -> list:
    """Ambil data realtime per well (GET dengan JSON body)"""
    if param is None:
        param = DEFAULT_PARAM

    payload = json.dumps({
        "token": token,
        "timeStart": start_time,
        "timeEnd": end_time,
        "param": param
    })
    headers = {"Content-Type": "application/json"}

    conn = http.client.HTTPSConnection(REALTIME_DATA_HOST)
    try:
        conn.request("GET", REALTIME_DATA_PATH, payload, headers)
        res = conn.getresponse()
        data = res.read()
        raw_response = data.decode(errors="replace")

        if res.status != 200:
            raise Exception(
                f"Fetch API failed: {res.status} {res.reason} | response={raw_response}"
            )

        return json.loads(raw_response).get("result", [])
    finally:
        conn.close()


async def fetch_all_wells_ops_realtime(start_time: str = None, end_time: str = None, param=None) -> list:
    """
    Ambil data realtime semua wells OPS, default 5 menit terakhir.

    Fungsional tetap:
    - Return tetap list all_data.
    - Scheduler lama tetap bisa pakai fungsi ini tanpa perubahan.

    Perubahan:
    - Jika 1 well error 404/no data, tampilkan notifikasi dan lanjut ke well berikutnya.
    - Jika 1 well error lain, tampilkan error dan lanjut ke well berikutnya.
    """
    if param is None:
        param = DEFAULT_PARAM

    now = datetime.utcnow()
    if not end_time:
        end_time = now.strftime("%Y-%m-%d %H:%M:%S")
    if not start_time:
        start_time = (now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")

    wells_ops = await fetch_wells_ops_list()
    all_data = []

    for idx, well in enumerate(wells_ops, start=1):
        wid = well.get("wid")
        well_name = well.get("well_name")
        token = well.get("is_api_token")

        print(f"[{idx}/{len(wells_ops)}] Fetch well OPS: {well_name} | wid={wid}")

        if not token:
            print(f"  -> SKIP: Token kosong / is_api_token tidak tersedia")
            continue

        try:
            well_data = await fetch_well_realtime(token, start_time, end_time, param)

            for record in well_data:
                record["wid"] = wid
                record["well_name"] = well_name

            all_data.extend(well_data)
            print(f"  -> OK: {len(well_data)} records")

        except Exception as e:
            error_message = str(e)

            if is_no_data_time_range_error(error_message):
                print(
                    f"  -> NO DATA: Well {well_name} | wid={wid} "
                    f"saat ini belum ada data yang bisa diprediksi "
                    f"pada range {start_time} sampai {end_time}"
                )
            else:
                print(
                    f"  -> ERROR: Well {well_name} | wid={wid} | {error_message}"
                )

            # Penting: jangan raise lagi, agar well lain tetap diproses.
            continue

    return all_data
