from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import engine
from app.models.article import Base
from app.core.scheduler import start_scheduler
from app.api.article import router as articles_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    from app.core.scheduler import scheduler
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
app.include_router(articles_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
