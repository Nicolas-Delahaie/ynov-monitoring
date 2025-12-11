from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
import logging
import json


from app.config import settings
from app.services.collector import GameplayCollector, inject_mock_metrics
from app.api import routes
from app.db import init_db, get_db  # Import de l'initialisation DB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

collector = GameplayCollector()
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting The Watchtower...")
    
    # Initialiser la base de données
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully!")
    

    # Connexion à NATS gérée par NomadStatsService
    from app.services.nomad_stats import NomadStatsService
    nomad_stats_service = NomadStatsService()
    await nomad_stats_service.connect_nats()
    logger.info("Connected to NATS server (via NomadStatsService)!")
    

    # Démarrer le scheduler
    scheduler.add_job(
        lambda: asyncio.create_task(nomad_stats_service.scheduled_collection()),
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
    await nomad_stats_service.close_nats()
    logger.info("Shutdown complete")

app = FastAPI(
    title="The Watchtower - CCC Monitoring",
    description="Monitoring and alerting system for Campus Clash Chronicles",
    version="1.0.0",
    lifespan=lifespan
)

# Prometheus instrumentation (doit être après la création de l'app)
Instrumentator().instrument(app).expose(app)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Injection automatique des métriques mock au démarrage (dev/demo)
inject_mock_metrics()
