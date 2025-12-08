from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
import logging
import json
from nats.aio.client import Client as NATS

from app.config import settings
from app.services.collector import GameplayCollector
from app.api import routes
from app.db import init_db, get_db  # Import de l'initialisation DB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

collector = GameplayCollector()
scheduler = AsyncIOScheduler()
nats_client = NATS()

async def scheduled_collection():
    """Collecte périodique des métriques et publication NATS"""
    logger.info("Starting scheduled metrics collection...")
    try:
        metrics = await collector.collect_all_metrics()
        logger.info(f"Collected metrics: {len(metrics)} categories")
        # Publication sur NATS
        if nats_client.is_connected:
            await nats_client.publish("metrics.watchtower", json.dumps(metrics).encode())
            logger.info("Metrics published to NATS on 'metrics.watchtower'")
    except Exception as e:
        logger.error(f"Error during scheduled collection: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting The Watchtower...")
    
    # Initialiser la base de données
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully!")
    
    # Connexion à NATS
    await nats_client.connect(servers=["nats://nats:4222"])
    logger.info("Connected to NATS server!")
    
    # Démarrer le scheduler
    scheduler.add_job(
        scheduled_collection,
        'interval',
        seconds=settings.METRICS_COLLECTION_INTERVAL
    )
    scheduler.start()
    logger.info(f"Scheduler started (interval: {settings.METRICS_COLLECTION_INTERVAL}s)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down The Watchtower...")
    scheduler.shutdown()
    # Fermer le client HTTP du collector
    await collector.client.aclose()
    if nats_client.is_connected:
        await nats_client.close()
    logger.info("Shutdown complete")

app = FastAPI(
    title="The Watchtower - CCC Monitoring",
    description="Monitoring and alerting system for Campus Clash Chronicles",
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

# Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# Routes
app.include_router(routes.router, prefix="/api", tags=["metrics"])

@app.get("/")
async def root():
    return {
        "service": "The Watchtower",
        "status": "operational",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
