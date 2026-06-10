# routes/predict_api_route.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from database.connection import get_db
from database.models import ActivityPrediction, CasingPrediction
from services.prediction_service import predict_batch_service, predict_batch_casing_service
from well_client.fetch_api import fetch_well_realtime, fetch_all_wells_ops_realtime
from well_client.mapping import ACTIVITY_FIELD_MAP, CASING_FIELD_MAP

router = APIRouter()

# ------------------- Input schema manual -------------------
class WellFetchInput(BaseModel):
    token: str = Field(..., description="API token well")
    start_time: str = Field(..., description="Start datetime, format YYYY-MM-DD HH:MM:SS")
    end_time: str = Field(..., description="End datetime, format YYYY-MM-DD HH:MM:SS")

# ------------------- Manual POST endpoints -------------------
@router.post("/predict-activity-api")
async def predict_activity_manual(input_data: WellFetchInput, db: Session = Depends(get_db)):
    raw_data = await fetch_well_realtime(input_data.token, input_data.start_time, input_data.end_time)
    if not raw_data:
        return {"success": True, "total_rows": 0, "results": []}

    sanitized = [
        {k: float(r.get(api_key, 0.0)) for api_key, k in ACTIVITY_FIELD_MAP.items()} 
        for r in raw_data
    ]
    results = predict_batch_service(sanitized)
    saved_results = []

    for inp, res in zip(sanitized, results):
        record = ActivityPrediction(
            **inp,
            prediction_code=res["prediction_code"],
            prediction_label=res["prediction_label"],
            confidence=res["confidence"],
            confidence_level=res["confidence_level"]
        )
        db.add(record)
        db.flush()
        saved_results.append({
            "input_data": inp,
            "prediction_code": res["prediction_code"],
            "prediction_label": res["prediction_label"],
            "confidence": res["confidence"]
        })

    db.commit()
    return {"success": True, "total_rows": len(saved_results), "results": saved_results}


@router.post("/predict-casing-api")
async def predict_casing_manual(input_data: WellFetchInput, db: Session = Depends(get_db)):
    raw_data = await fetch_well_realtime(input_data.token, input_data.start_time, input_data.end_time)
    if not raw_data:
        return {"success": True, "total_rows": 0, "results": []}

    sanitized = [
        {k: float(r.get(api_key, 0.0)) for api_key, k in CASING_FIELD_MAP.items()} 
        for r in raw_data
    ]
    results = predict_batch_casing_service(sanitized)
    saved_results = []

    for inp, res in zip(sanitized, results):
        record = CasingPrediction(
            **inp,
            prediction_code=res["prediction_code"],
            prediction_label=res["prediction_label"],
            confidence=res["confidence"],
            confidence_level=res["confidence_level"]
        )
        db.add(record)
        db.flush()
        saved_results.append({
            "input_data": inp,
            "prediction_code": res["prediction_code"],
            "prediction_label": res["prediction_label"],
            "confidence": res["confidence"]
        })

    db.commit()
    return {"success": True, "total_rows": len(saved_results), "results": saved_results}


# ------------------- Batch OPS endpoints -------------------
@router.post("/predict-activity-ops")
async def predict_activity_ops(db: Session = Depends(get_db)):
    data_list = await fetch_all_wells_ops_realtime()
    if not data_list:
        return {"success": True, "total_rows": 0, "results": []}

    # Ambil hanya 5 menit terakhir
    now = datetime.utcnow()
    five_minutes_ago = now - timedelta(minutes=5)
    filtered_data = [
        r for r in data_list if "dt" in r and datetime.strptime(r["dt"], "%Y-%m-%d %H:%M:%S") >= five_minutes_ago
    ]

    sanitized = [
        {k: float(r.get(api_key, 0.0)) for api_key, k in ACTIVITY_FIELD_MAP.items()} | {"well_name": r.get("well_name")}
        for r in filtered_data
    ]
    results = predict_batch_service(sanitized)
    saved_results = []

    for inp, res in zip(sanitized, results):
        record = ActivityPrediction(
            **{k: v for k, v in inp.items() if k != "well_name"},
            prediction_code=res["prediction_code"],
            prediction_label=res["prediction_label"],
            confidence=res["confidence"],
            confidence_level=res["confidence_level"]
        )
        db.add(record)
        db.flush()
        saved_results.append({
            "well_name": inp.get("well_name"),
            "input_data": {k: v for k, v in inp.items() if k != "well_name"},
            "prediction_code": res["prediction_code"],
            "prediction_label": res["prediction_label"],
            "confidence": res["confidence"]
        })

    db.commit()
    return {"success": True, "total_rows": len(saved_results), "results": saved_results}


@router.post("/predict-casing-ops")
async def predict_casing_ops(db: Session = Depends(get_db)):
    data_list = await fetch_all_wells_ops_realtime()
    if not data_list:
        return {"success": True, "total_rows": 0, "results": []}

    # Ambil hanya 5 menit terakhir
    now = datetime.utcnow()
    five_minutes_ago = now - timedelta(minutes=5)
    filtered_data = [
        r for r in data_list if "dt" in r and datetime.strptime(r["dt"], "%Y-%m-%d %H:%M:%S") >= five_minutes_ago
    ]

    sanitized = [
        {k: float(r.get(api_key, 0.0)) for api_key, k in CASING_FIELD_MAP.items()} | {"well_name": r.get("well_name")}
        for r in filtered_data
    ]
    results = predict_batch_casing_service(sanitized)
    saved_results = []

    for inp, res in zip(sanitized, results):
        record = CasingPrediction(
            **{k: v for k, v in inp.items() if k != "well_name"},
            prediction_code=res["prediction_code"],
            prediction_label=res["prediction_label"],
            confidence=res["confidence"],
            confidence_level=res["confidence_level"]
        )
        db.add(record)
        db.flush()
        saved_results.append({
            "well_name": inp.get("well_name"),
            "input_data": {k: v for k, v in inp.items() if k != "well_name"},
            "prediction_code": res["prediction_code"],
            "prediction_label": res["prediction_label"],
            "confidence": res["confidence"]
        })

    db.commit()
    return {"success": True, "total_rows": len(saved_results), "results": saved_results}