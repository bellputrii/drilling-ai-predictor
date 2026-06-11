# scheduler/realtime_scheduler_separated_pretty.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from database.connection import SessionLocal
from database.models import ActivityPrediction, CasingPrediction
from services.prediction_service import predict_batch_service, predict_batch_casing_service
from well_client.fetch_api import fetch_all_wells_ops_realtime
from well_client.mapping import ACTIVITY_FIELD_MAP, CASING_FIELD_MAP


def sanitize_input(record: dict, field_map: dict) -> dict:
    """Mapping API keys ke schema FastAPI"""
    return {fastapi_key: float(record.get(api_key, 0.0)) for api_key, fastapi_key in field_map.items()}


# =========================
# TAMBAHAN: helper scheduler
# =========================

def normalize_fetch_result(fetch_result):
    """
    Menyesuaikan hasil dari fetch_all_wells_ops_realtime.

    Support:
    1. Return lama:
       data_list = [...]

    2. Return baru:
       {
           "data": [...],
           "errors": [...],
           "summary_per_well": [...]
       }
    """
    if isinstance(fetch_result, dict):
        data_list = fetch_result.get("data", []) or []
        errors = fetch_result.get("errors", []) or []
        summary_per_well = fetch_result.get("summary_per_well", []) or []
        return data_list, errors, summary_per_well

    if isinstance(fetch_result, list):
        return fetch_result, [], []

    return [], [{"error": f"Unexpected fetch result type: {type(fetch_result)}"}], []


def is_no_data_time_range_error(error_message: str) -> bool:
    """
    Deteksi error API ketika tidak ada data pada range waktu tertentu.
    """
    if not error_message:
        return False

    message = str(error_message).lower()

    return (
        "404" in message
        or "not found" in message
        or "no data found for the given time range" in message
        or "no data" in message
    )


def print_fetch_error_notifications(module_name: str, errors: list):
    """
    Tampilkan notifikasi error per well tanpa menghentikan scheduler.
    """
    if not errors:
        return

    for err in errors:
        well_name = err.get("well_name", "Unknown Well")
        wid = err.get("wid", "-")
        error_message = err.get("error", "")

        if is_no_data_time_range_error(error_message):
            print(
                f"[{module_name} Scheduler] Notification: "
                f"Well {well_name} | wid={wid} saat ini belum ada data yang bisa diprediksi "
                f"pada range waktu yang diminta."
            )
        else:
            print(
                f"[{module_name} Scheduler] Fetch Error: "
                f"Well {well_name} | wid={wid} | {error_message}"
            )


def print_fetch_summary(module_name: str, summary_per_well: list):
    """
    Tampilkan ringkasan jumlah record per well.
    """
    if not summary_per_well:
        return

    print(f"\n[{module_name} Scheduler] Fetch Summary Per Well:")
    for item in summary_per_well:
        print(
            f"- {item.get('well_name')} | "
            f"wid={item.get('wid')} | "
            f"records={item.get('records')}"
        )


def get_activity_api_scheduler(interval_minutes: int = 1):
    scheduler = AsyncIOScheduler()

    async def scheduled_task():
        try:
            fetch_result = await fetch_all_wells_ops_realtime()
            data_list, fetch_errors, summary_per_well = normalize_fetch_result(fetch_result)

            print_fetch_error_notifications("Activity", fetch_errors)
            print_fetch_summary("Activity", summary_per_well)

            if not data_list:
                print("[Activity Scheduler] No data.")
                return

            now = datetime.utcnow()
            five_minutes_ago = now - timedelta(minutes=5)
            filtered = [r for r in data_list if "dt" in r and datetime.strptime(r["dt"], "%Y-%m-%d %H:%M:%S") >= five_minutes_ago]
            if not filtered:
                print("[Activity Scheduler] No data in last 5 minutes.")
                return

            db = SessionLocal()
            try:
                sanitized_data = [sanitize_input(r, ACTIVITY_FIELD_MAP) | {"well_name": r.get("well_name")} for r in filtered]
                results = predict_batch_service(sanitized_data)

                for idx, (inp, res) in enumerate(zip(sanitized_data, results), start=1):
                    record = ActivityPrediction(
                        **{k: v for k, v in inp.items() if k != "well_name"},
                        prediction_code=res["prediction_code"],
                        prediction_label=res["prediction_label"],
                        confidence=res["confidence"],
                        confidence_level=res["confidence_level"]
                    )
                    db.add(record)
                    db.flush()

                    # Pretty print
                    print(
                        f"""
--------------------------------------------------
Activity Prediction #{idx} (Well: {inp['well_name']})
MD         : {inp.get('md')}
Blockpos   : {inp.get('blockpos')}
Bit Depth  : {inp.get('bitdepth')}
Hookload   : {inp.get('Hookload')}
RPM        : {inp.get('rpm')}
Torqa      : {inp.get('torqa')}
WOB        : {inp.get('woba')}
ROP        : {inp.get('rop')}
STP PRESS  : {inp.get('stppress')}
Mudflowin  : {inp.get('mudflowin')}

Prediction : {res['prediction_label']}
Code       : {res['prediction_code']}
Confidence : {res['confidence']:.4f}
--------------------------------------------------
"""
                    )

                db.commit()
            finally:
                db.close()
        except Exception as e:
            print("[Activity Scheduler] Error:", e)

    scheduler.add_job(scheduled_task, trigger=IntervalTrigger(minutes=interval_minutes), id="activity_task", name="Activity Scheduler")
    return scheduler


def get_casing_api_scheduler(interval_minutes: int = 1):
    scheduler = AsyncIOScheduler()

    async def scheduled_task():
        try:
            fetch_result = await fetch_all_wells_ops_realtime()
            data_list, fetch_errors, summary_per_well = normalize_fetch_result(fetch_result)

            print_fetch_error_notifications("Casing", fetch_errors)
            print_fetch_summary("Casing", summary_per_well)

            if not data_list:
                print("[Casing Scheduler] No data.")
                return

            now = datetime.utcnow()
            five_minutes_ago = now - timedelta(minutes=5)
            filtered = [r for r in data_list if "dt" in r and datetime.strptime(r["dt"], "%Y-%m-%d %H:%M:%S") >= five_minutes_ago]
            if not filtered:
                print("[Casing Scheduler] No data in last 5 minutes.")
                return

            db = SessionLocal()
            try:
                sanitized_data = [sanitize_input(r, CASING_FIELD_MAP) | {"well_name": r.get("well_name")} for r in filtered]
                results = predict_batch_casing_service(sanitized_data)

                for idx, (inp, res) in enumerate(zip(sanitized_data, results), start=1):
                    record = CasingPrediction(
                        **{k: v for k, v in inp.items() if k != "well_name"},
                        prediction_code=res["prediction_code"],
                        prediction_label=res["prediction_label"],
                        confidence=res["confidence"],
                        confidence_level=res["confidence_level"]
                    )
                    db.add(record)
                    db.flush()

                    # Pretty print
                    print(
                        f"""
--------------------------------------------------
Casing Prediction #{idx} (Well: {inp['well_name']})
Blockpos   : {inp.get('blockpos')}
Bit Depth  : {inp.get('bitdepth')}
MD         : {inp.get('md')}
STP Press  : {inp.get('stppress')}
Speed Down : {inp.get('speeddown')}
Speed Up   : {inp.get('speedup')}
HKLDA      : {inp.get('hklda')}
Mudflowin  : {inp.get('mudflowin')}

Prediction : {res['prediction_label']}
Code       : {res['prediction_code']}
Confidence : {res['confidence']:.4f}
--------------------------------------------------
"""
                    )

                db.commit()
            finally:
                db.close()
        except Exception as e:
            print("[Casing Scheduler] Error:", e)

    scheduler.add_job(scheduled_task, trigger=IntervalTrigger(minutes=interval_minutes), id="casing_task", name="Casing Scheduler")
    return scheduler
