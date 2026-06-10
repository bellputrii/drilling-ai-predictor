# scheduler/realtime_scheduler_separated.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from database.connection import SessionLocal
from database.models import ActivityPrediction, CasingPrediction
from services.prediction_service import predict_batch_service, predict_batch_casing_service
from well_client.fetch_api import fetch_all_wells_ops_realtime
from well_client.mapping import ACTIVITY_FIELD_MAP, CASING_FIELD_MAP

def sanitize_input(record: dict, field_map: dict) -> dict:
    """Mapping API ke schema FastAPI (Activity/Casing)"""
    return {fastapi_key: float(record.get(api_key, 0.0)) for api_key, fastapi_key in field_map.items()}

def get_activity_api_scheduler(interval_minutes: int = 1):
    scheduler = AsyncIOScheduler()

    async def scheduled_task():
        try:
            data_list = await fetch_all_wells_ops_realtime()
            if not data_list:
                print("[Activity Scheduler] No data in this interval.")
                return

            # Filter 5 menit terakhir
            now = datetime.utcnow()
            five_minutes_ago = now - timedelta(minutes=5)
            filtered_data = [
                r for r in data_list if "dt" in r and datetime.strptime(r["dt"], "%Y-%m-%d %H:%M:%S") >= five_minutes_ago
            ]
            if not filtered_data:
                print("[Activity Scheduler] No data in last 5 minutes.")
                return

            db = SessionLocal()
            try:
                sanitized_activity = [
                    sanitize_input(r, ACTIVITY_FIELD_MAP) | {"well_name": r.get("well_name")}
                    for r in filtered_data
                ]
                results_activity = predict_batch_service(sanitized_activity)

                for inp, res in zip(sanitized_activity, results_activity):
                    record = ActivityPrediction(
                        **{k: v for k, v in inp.items() if k != "well_name"},
                        prediction_code=res["prediction_code"],
                        prediction_label=res["prediction_label"],
                        confidence=res["confidence"],
                        confidence_level=res["confidence_level"]
                    )
                    db.add(record)
                    db.flush()
                    print({
                        "well_name": inp["well_name"],
                        "input_data": {k: v for k, v in inp.items() if k != "well_name"},
                        "prediction_code": res["prediction_code"],
                        "prediction_label": res["prediction_label"],
                        "confidence": res["confidence"]
                    })

                db.commit()

            finally:
                db.close()

        except Exception as e:
            print("[Activity Scheduler] Error:", e)

    scheduler.add_job(
        scheduled_task,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="realtime_activity_task",
        name="Realtime Activity Prediction"
    )
    return scheduler

def get_casing_api_scheduler(interval_minutes: int = 1):
    scheduler = AsyncIOScheduler()

    async def scheduled_task():
        try:
            data_list = await fetch_all_wells_ops_realtime()
            if not data_list:
                print("[Casing Scheduler] No data in this interval.")
                return

            # Filter 5 menit terakhir
            now = datetime.utcnow()
            five_minutes_ago = now - timedelta(minutes=5)
            filtered_data = [
                r for r in data_list if "dt" in r and datetime.strptime(r["dt"], "%Y-%m-%d %H:%M:%S") >= five_minutes_ago
            ]
            if not filtered_data:
                print("[Casing Scheduler] No data in last 5 minutes.")
                return

            db = SessionLocal()
            try:
                sanitized_casing = [
                    sanitize_input(r, CASING_FIELD_MAP) | {"well_name": r.get("well_name")}
                    for r in filtered_data
                ]
                results_casing = predict_batch_casing_service(sanitized_casing)

                for inp, res in zip(sanitized_casing, results_casing):
                    record = CasingPrediction(
                        **{k: v for k, v in inp.items() if k != "well_name"},
                        prediction_code=res["prediction_code"],
                        prediction_label=res["prediction_label"],
                        confidence=res["confidence"],
                        confidence_level=res["confidence_level"]
                    )
                    db.add(record)
                    db.flush()
                    print({
                        "well_name": inp["well_name"],
                        "input_data": {k: v for k, v in inp.items() if k != "well_name"},
                        "prediction_code": res["prediction_code"],
                        "prediction_label": res["prediction_label"],
                        "confidence": res["confidence"]
                    })

                db.commit()

            finally:
                db.close()

        except Exception as e:
            print("[Casing Scheduler] Error:", e)

    scheduler.add_job(
        scheduled_task,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="realtime_casing_task",
        name="Realtime Casing Prediction"
    )
    return scheduler