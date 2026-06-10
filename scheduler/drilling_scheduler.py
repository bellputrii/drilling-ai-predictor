import json
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from services.prediction_service import predict_batch_service
from database.connection import SessionLocal
from database.models import ActivityPrediction


def get_scheduler():
    """
    Membuat scheduler baru dengan job batch prediksi drilling activity.
    """
    scheduler = AsyncIOScheduler()

    async def scheduled_prediction_task():
        print("Scheduler triggered!")

        # Gunakan path relatif agar deployment fleksibel
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts", "drilling_data.json")

        # Baca JSON lokal
        try:
            with open(json_path, "r") as f:
                input_items = json.load(f)
        except Exception as e:
            print("Failed to read drilling_data.json:", e)
            return

        # Jalankan batch prediksi
        results = predict_batch_service(input_items)

        # # Simpan ke DB
        # db = SessionLocal()
        # try:
        #     for input_dict, result in zip(input_items, results):
        #         try:
        #             # Ambil hanya field yang ada di ActivityPrediction
        #             record_data = {k: input_dict[k] for k in [
        #                 "bitdepth", "md", "Hookload", "mudflowin",
        #                 "rpm", "torqa", "woba", "blockpos"
        #             ]}
        #             record_data.update({
        #                 "prediction_code": result["prediction_code"],
        #                 "prediction_label": result["prediction_label"],
        #                 "confidence": result["confidence"],
        #                 "confidence_level": result.get("confidence_level", "Unknown")
        #             })
        #             record = ActivityPrediction(**record_data)
        #             db.add(record)
                    
        #         except Exception as e:
        #             print("Failed to insert record:", result, e)
        #     db.commit()
        #     print(f"{len(results)} records saved by scheduler")
        # except Exception as e:
        #     db.rollback()
        #     print("Error during batch commit:", e)
        # finally:
        #     db.close()

        # Simpan ke DB
        db = SessionLocal()

        try:
            for idx, (input_dict, result) in enumerate(zip(input_items, results), start=1):
                try:
                    # Ambil hanya field yang ada di ActivityPrediction
                    record_data = {k: input_dict[k] for k in [
                        "bitdepth", "md", "Hookload", "mudflowin",
                        "rpm", "torqa", "woba", "blockpos", "rop", "stppress"
                    ]}

                    record_data.update({
                        "prediction_code": result["prediction_code"],
                        "prediction_label": result["prediction_label"],
                        "confidence": result["confidence"],
                        "confidence_level": result.get("confidence_level", "Unknown")
                    })

                    record = ActivityPrediction(**record_data)
                    db.add(record)

                    # ==========================================
                    # DETAIL PREDICTION LOG
                    # ==========================================
                    print(
                        f"""
        --------------------------------------------------
        Prediction #{idx}
        MD         : {input_dict['md']}
        Bit Depth  : {input_dict['bitdepth']}
        Hookload   : {input_dict['Hookload']}
        RPM        : {input_dict['rpm']}
        WOB        : {input_dict['woba']}

        Prediction : {result['prediction_label']}
        Code       : {result['prediction_code']}
        Confidence : {result['confidence']:.4f}
        --------------------------------------------------
        """
                    )

                except Exception as e:
                    print("Failed to insert record:", result, e)

            db.commit()

            # ==========================================
            # SUMMARY
            # ==========================================
            total_records = db.query(ActivityPrediction).count()

            print("\n" + "=" * 60)
            print("BATCH PREDICTION COMPLETED")
            print(f"Total Predictions This Run : {len(results)}")
            print(f"Total Records In SQLite    : {total_records}")
            print("Status                    : Saved Successfully")
            print("=" * 60 + "\n")

        except Exception as e:
            db.rollback()
            print("Error during batch commit:", e)

        finally:
            db.close()

    # Tambahkan job scheduler
    scheduler.add_job(
        scheduled_prediction_task,
        trigger=IntervalTrigger(minutes=1),
        id="drilling_prediction_task",
        name="Scheduled batch drilling prediction"
    )

    return scheduler