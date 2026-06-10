from database.connection import engine, Base
from database import models
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.predict_api import router as predict_router
from routes.activity_route import router as activity_router

# Import scheduler
from scheduler.casing_scheduler import get_casing_scheduler
from scheduler.drilling_scheduler import get_scheduler
from scheduler.realtime_scheduler import get_activity_api_scheduler
from scheduler.realtime_scheduler import get_casing_api_scheduler

app = FastAPI(
    title="Drilling Activity and Casing Trip API Classifier",
    description="API untuk prediksi activity drilling dan casing trip menggunakan Random Forest ONNX",
    version="1.5.0"
)

# Buat table DB otomatis
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(activity_router)
app.include_router(predict_router)

activity_api_scheduler = get_activity_api_scheduler()
casing_api_scheduler = get_casing_api_scheduler()

# scheduler = get_scheduler()
# casing_scheduler = get_casing_scheduler()

@app.on_event("startup")
async def start_scheduler():
    # scheduler.start()
    # casing_scheduler.start()
    activity_api_scheduler.start()
    casing_api_scheduler.start()