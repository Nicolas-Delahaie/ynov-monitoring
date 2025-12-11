import httpx
from prometheus_client import Counter, Histogram, Gauge
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
from app.config import settings
import logging
import os
import time

logger = logging.getLogger(__name__)

# Métriques Prometheus (garde l'existant)
nomad_actions = Counter(
    'ccc_nomad_actions_total',
    'Total number of nomad actions',
    ['action_type', 'player_id']
)

resource_collected = Counter(
    'ccc_resources_collected_total',
    'Total resources collected',
    ['resource_type', 'player_id']
)

dwelling_levels = Gauge(
    'ccc_dwelling_levels',
    'Current dwelling levels',
    ['player_id']
)

active_nomads = Gauge(
    'ccc_active_nomads',
    'Number of active nomads',
    ['player_id']
)

pvp_actions = Counter(
    'ccc_pvp_actions_total',
    'Total PvP actions',
    ['action_type']
)

event_triggers = Counter(
    'ccc_events_triggered_total',
    'Total game events triggered',
    ['event_type']
)

api_response_time = Histogram(
    'ccc_api_response_seconds',
    'API response time',
    ['endpoint']
)

# Nouveau: métrique pour les erreurs d'API
api_errors = Counter(
    'ccc_api_errors_total',
    'Total API errors',
    ['endpoint', 'error_type']
)

class GameplayCollector:
    def __init__(self):
        headers = {}
        if settings.CCC_API_KEY:
            headers['Authorization'] = f'Bearer {settings.CCC_API_KEY}'
        
        self.client = httpx.AsyncClient(
            base_url=settings.CCC_API_URL,
            timeout=30.0,
            headers=headers
        )
    
    async def _make_request(self, endpoint: str) -> Optional[Dict]:
        """Effectue une requête à l'API avec gestion d'erreurs améliorée"""
        start_time = datetime.now()
        
        try:
            response = await self.client.get(endpoint)
            
            # Mesurer le temps de réponse
            duration = (datetime.now() - start_time).total_seconds()
            api_response_time.labels(endpoint=endpoint).observe(duration)
            
            # Vérifier le code de statut
            if response.status_code == 404:
                logger.warning(f"Endpoint not found: {endpoint}")
                api_errors.labels(endpoint=endpoint, error_type="not_found").inc()
                return None
            
            if response.status_code == 401:
                logger.error(f"Unauthorized access to {endpoint} - Check API key")
                api_errors.labels(endpoint=endpoint, error_type="unauthorized").inc()
                return None
            
            if response.status_code >= 500:
                logger.error(f"Server error on {endpoint}: {response.status_code}")
                api_errors.labels(endpoint=endpoint, error_type="server_error").inc()
                return None
            
            response.raise_for_status()
            return response.json()
            
        except httpx.TimeoutException:
            logger.error(f"Timeout on endpoint: {endpoint}")
            api_errors.labels(endpoint=endpoint, error_type="timeout").inc()
            return None
            
        except httpx.NetworkError as e:
            logger.error(f"Network error on {endpoint}: {e}")
            api_errors.labels(endpoint=endpoint, error_type="network_error").inc()
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error on {endpoint}: {e}")
            api_errors.labels(endpoint=endpoint, error_type="unknown").inc()
            return None
    
    async def collect_nomad_metrics(self) -> Dict:
        """Collecte les métriques des Nomads"""
        try:
            data = await self._make_request("/nomads")
            
            if data is None:
                return {"status": "error", "message": "Failed to fetch nomad data"}
            
            # Traiter les données
            for nomad in data.get('nomads', []):
                nomad_actions.labels(
                    action_type=nomad.get('action_type', 'unknown'),
                    player_id=nomad.get('player_id', 'unknown')
                ).inc()
            
            active_nomads.labels(player_id='all').set(len(data.get('nomads', [])))
            
            return {
                "status": "success",
                "total_nomads": len(data.get('nomads', [])),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error collecting nomad metrics: {e}")
            return {"status": "error", "message": str(e)}
    
    async def collect_resource_metrics(self) -> Dict:
        """Collecte les métriques des ressources"""
        try:
            data = await self._make_request("/resources")
            
            if data is None:
                return {"status": "error", "message": "Failed to fetch resource data"}
            
            for resource in data.get('resources', []):
                resource_collected.labels(
                    resource_type=resource.get('type', 'unknown'),
                    player_id=resource.get('player_id', 'unknown')
                ).inc(resource.get('amount', 0))
            
            return {
                "status": "success",
                "total_resources": len(data.get('resources', [])),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error collecting resource metrics: {e}")
            return {"status": "error", "message": str(e)}
    
    async def collect_dwelling_metrics(self) -> Dict:
        """Collecte les métriques des Dwellings"""
        try:
            data = await self._make_request("/dwellings")
            
            if data is None:
                return {"status": "error", "message": "Failed to fetch dwelling data"}
            
            for dwelling in data.get('dwellings', []):
                dwelling_levels.labels(
                    player_id=dwelling.get('player_id', 'unknown')
                ).set(dwelling.get('level', 0))
            
            return {
                "status": "success",
                "total_dwellings": len(data.get('dwellings', [])),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error collecting dwelling metrics: {e}")
            return {"status": "error", "message": str(e)}
    
    async def collect_pvp_metrics(self) -> Dict:
        """Collecte les métriques PvP"""
        try:
            data = await self._make_request("/pvp")
            
            if data is None:
                return {"status": "error", "message": "Failed to fetch PvP data"}
            
            for action in data.get('pvp_actions', []):
                pvp_actions.labels(
                    action_type=action.get('type', 'unknown')
                ).inc()
            
            return {
                "status": "success",
                "total_pvp_actions": len(data.get('pvp_actions', [])),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error collecting PvP metrics: {e}")
            return {"status": "error", "message": str(e)}
    
    async def collect_event_metrics(self) -> Dict:
        """Collecte les métriques des événements"""
        try:
            data = await self._make_request("/events")
            
            if data is None:
                return {"status": "error", "message": "Failed to fetch event data"}
            
            for event in data.get('events', []):
                event_triggers.labels(
                    event_type=event.get('type', 'unknown')
                ).inc()
            
            return {
                "status": "success",
                "total_events": len(data.get('events', [])),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error collecting event metrics: {e}")
            return {"status": "error", "message": str(e)}
    
    async def collect_all_metrics(self) -> Dict:
        """Collecte toutes les métriques en parallèle"""
        try:
            results = await asyncio.gather(
                self.collect_nomad_metrics(),
                self.collect_resource_metrics(),
                self.collect_dwelling_metrics(),
                self.collect_pvp_metrics(),
                self.collect_event_metrics(),
                return_exceptions=True
            )
            
            return {
                "nomads": results[0] if not isinstance(results[0], Exception) else {"status": "error"},
                "resources": results[1] if not isinstance(results[1], Exception) else {"status": "error"},
                "dwellings": results[2] if not isinstance(results[2], Exception) else {"status": "error"},
                "pvp": results[3] if not isinstance(results[3], Exception) else {"status": "error"},
                "events": results[4] if not isinstance(results[4], Exception) else {"status": "error"},
                "collection_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Critical error in collect_all_metrics: {e}")
            return {"status": "error", "message": str(e)}

            
def inject_mock_metrics():
    """
    Injecte des métriques Prometheus fictives pour le dashboard Grafana (dev/demo), réparties depuis 9h ce matin.
    """
    now = datetime.utcnow()
    # Heure de début : aujourd'hui 9h UTC
    start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if start > now:
        start -= timedelta(days=1)
    # Génère des points toutes les 20 minutes
    points = int(((now - start).total_seconds()) // (20 * 60))
    for i in range(points):
        # t = start + timedelta(minutes=20 * i)
        # ts = time.mktime(t.timetuple())
        # 3 types d'actions, 7 users
        for a in range(3):
            for u in range(7):
                nomad_actions.labels(action_type=f"move_{a}", player_id=f"user_{u}").inc(5 + (a + u + i) % 10)
    for i in range(5):
        resource_collected.labels(resource_type=f"gold_{i%2}", player_id=f"user_{i%3}").inc(10 + i)
    for i in range(3):
        dwelling_levels.labels(player_id=f"user_{i}").set(1 + i)
    active_nomads.labels(player_id='all').set(7)
    for i in range(4):
        pvp_actions.labels(action_type=f"attack_{i%2}").inc(2 + i)
    for i in range(3):
        event_triggers.labels(event_type=f"event_{i}").inc(1)
    for i in range(10):
        api_response_time.labels(endpoint=f"/api/test_{i%2}").observe(0.1 + 0.05 * (i % 3))
    for i in range(2):
        api_errors.labels(endpoint=f"/api/test_{i}", error_type="timeout").inc(1)

# Appelle cette fonction au démarrage (dev uniquement)
if os.environ.get("INJECT_MOCK_METRICS", "1") == "1":
    inject_mock_metrics()
