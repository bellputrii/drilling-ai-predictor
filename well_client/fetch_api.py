import http.client
import json
from datetime import datetime, timedelta

REALTIME_DATA_HOST = "pdumitradome.id"
REALTIME_DATA_PATH = "/dome_api/realtime-data"
WELLS_ACTIVE_PATH = "/dome_api/wells-active"

DEFAULT_PARAM = [
    "dt","md","bitdepth","blockpos","hklda","mudflowin",
    "ropi","rpm","torqa","stppress","woba","speedup","speeddown","md"
]

async def fetch_wells_active() -> list:
    """Ambil semua wells"""
    conn = http.client.HTTPSConnection(REALTIME_DATA_HOST)
    conn.request("GET", WELLS_ACTIVE_PATH, "", {})
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode()).get("result", [])

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
    conn.request("GET", REALTIME_DATA_PATH, payload, headers)
    res = conn.getresponse()
    if res.status != 200:
        raise Exception(f"Fetch API failed: {res.status} {res.reason}")
    data = res.read()
    return json.loads(data.decode()).get("result", [])

async def fetch_all_wells_ops_realtime(start_time: str = None, end_time: str = None, param=None) -> list:
    """Ambil data realtime semua wells OPS, default 1 jam terakhir"""
    if param is None:
        param = DEFAULT_PARAM

    now = datetime.utcnow()
    if not end_time:
        end_time = now.strftime("%Y-%m-%d %H:%M:%S")
    if not start_time:
        start_time = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

    wells_ops = await fetch_wells_ops_list()
    all_data = []
    for well in wells_ops:
        token = well.get("is_api_token")
        if not token:
            continue
        well_data = await fetch_well_realtime(token, start_time, end_time, param)
        for record in well_data:
            record["wid"] = well.get("wid")
            record["well_name"] = well.get("well_name")
        all_data.extend(well_data)
    return all_data