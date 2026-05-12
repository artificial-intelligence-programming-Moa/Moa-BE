from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.database import SessionLocal
from app.services.pipeline_service import run_pipeline

scheduler = AsyncIOScheduler()

def scheduled_job():
    db = SessionLocal()
    try:
        run_pipeline(db)
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(scheduled_job, "interval", hours=1)
    scheduler.start()
    print("[scheduler] 1시간 간격으로 실행 시작")