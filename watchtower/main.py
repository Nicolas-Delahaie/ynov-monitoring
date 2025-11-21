from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
import logging

from watchtower.config import settings
from watchtower.services.collector import GameplayCollector
from watchtower.api import routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

collector = GameplayCollector()
scheduler = AsyncIOScheduler()

async def scheduled_collection():
    """Collecte périodique des métriques"""
    logger.info("Starting scheduled metrics collection...")
    metrics = await collector.collect_all_metrics()
    logger.info(f"Collected metrics: {len(metrics)} categories")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting The Watchtower...")
    scheduler.add_job(
        scheduled_collection,
        'interval',
        seconds=settings.METRICS_COLLECTION_INTERVAL
    )
    scheduler.start()
    yield
    # Shutdown
    logger.info("Shutting down The Watchtower...")
    scheduler.shutdown()
    await collector.close()

app = FastAPI(
    title="The Watchtower",
    description="Service de monitoring et d'alerting gameplay pour CCC",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrumentation Prometheus
Instrumentator().instrument(app).expose(app)

# Routes
app.include_router(routes.router, prefix="/api/v1", tags=["metrics"])

@app.get("/")
async def root():
    return {
        "service": "The Watchtower",
        "status": "operational",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
