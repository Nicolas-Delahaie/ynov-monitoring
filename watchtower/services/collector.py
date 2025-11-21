import httpx
from prometheus_client import Counter, Histogram, Gauge
from datetime import datetime
from typing import Dict, List
import asyncio
from watchtower.config import settings
import logging

logger = logging.getLogger(__name__)

# Prometheus metrics
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

class GameplayCollector:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.CCC_API_URL,
            timeout=30.0,
            headers={"Authorization": f"Bearer {settings.CCC_API_KEY}"} if settings.CCC_API_KEY else {}
        )
        self.cache = {}
    
    async def collect_nomad_metrics(self) -> Dict:
        """Collecte les métriques des actions Nomads"""
        try:
            with api_response_time.labels(endpoint='/nomads').time():
                response = await self.client.get("/nomads")
                response.raise_for_status()
                data = response.json()
            
            metrics = {
                'total_nomads': len(data.get('nomads', [])),
                'by_action': {},
                'by_player': {}
            }
            
            for nomad in data.get('nomads', []):
                player_id = nomad.get('player_id')
                action = nomad.get('last_action')
                
                if action:
                    nomad_actions.labels(
                        action_type=action,
                        player_id=player_id
                    ).inc()
                    
                    metrics['by_action'][action] = metrics['by_action'].get(action, 0) + 1
                
                active_nomads.labels(player_id=player_id).set(
                    nomad.get('count', 1)
                )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting nomad metrics: {e}")
            return {}
    
    async def collect_resource_metrics(self) -> Dict:
        """Collecte les métriques de ressources"""
        try:
            with api_response_time.labels(endpoint='/resources').time():
                response = await self.client.get("/resources")
                response.raise_for_status()
                data = response.json()
            
            metrics = {
                'total_gold': 0,
                'total_spice': 0,
                'by_player': {}
            }
            
            for player_data in data.get('players', []):
                player_id = player_data.get('player_id')
                gold = player_data.get('gold', 0)
                spice = player_data.get('spice', 0)
                
                resource_collected.labels(
                    resource_type='gold',
                    player_id=player_id
                ).inc(gold)
                
                resource_collected.labels(
                    resource_type='spice',
                    player_id=player_id
                ).inc(spice)
                
                metrics['total_gold'] += gold
                metrics['total_spice'] += spice
                metrics['by_player'][player_id] = {
                    'gold': gold,
                    'spice': spice
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting resource metrics: {e}")
            return {}
    
    async def collect_dwelling_metrics(self) -> Dict:
        """Collecte les métriques des Dwellings"""
        try:
            with api_response_time.labels(endpoint='/dwellings').time():
                response = await self.client.get("/dwellings")
                response.raise_for_status()
                data = response.json()
            
            metrics = {
                'by_level': {1: 0, 2: 0, 3: 0, 4: 0},
                'total': 0
            }
            
            for dwelling in data.get('dwellings', []):
                player_id = dwelling.get('player_id')
                level = dwelling.get('level', 1)
                
                dwelling_levels.labels(player_id=player_id).set(level)
                
                metrics['by_level'][level] = metrics['by_level'].get(level, 0) + 1
                metrics['total'] += 1
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting dwelling metrics: {e}")
            return {}
    
    async def collect_pvp_metrics(self) -> Dict:
        """Collecte les métriques PvP"""
        try:
            with api_response_time.labels(endpoint='/pvp').time():
                response = await self.client.get("/combat/stats")
                response.raise_for_status()
                data = response.json()
            
            metrics = {
                'total_attacks': 0,
                'successful_attacks': 0,
                'destroyed_dwellings': 0
            }
            
            for combat in data.get('combats', []):
                action_type = combat.get('type', 'attack')
                success = combat.get('success', False)
                
                pvp_actions.labels(action_type=action_type).inc()
                
                metrics['total_attacks'] += 1
                if success:
                    metrics['successful_attacks'] += 1
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting PvP metrics: {e}")
            return {}
    
    async def collect_event_metrics(self) -> Dict:
        """Collecte les métriques des événements"""
        try:
            with api_response_time.labels(endpoint='/events').time():
                response = await self.client.get("/events")
                response.raise_for_status()
                data = response.json()
            
            metrics = {
                'by_type': {},
                'total': 0
            }
            
            for event in data.get('events', []):
                event_type = event.get('type')
                affected = event.get('affected_players', 0)
                
                event_triggers.labels(event_type=event_type).inc()
                
                metrics['by_type'][event_type] = {
                    'count': metrics['by_type'].get(event_type, {}).get('count', 0) + 1,
                    'affected_players': affected
                }
                metrics['total'] += 1
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting event metrics: {e}")
            return {}
    
    async def collect_all_metrics(self) -> Dict:
        """Collecte toutes les métriques en parallèle"""
        results = await asyncio.gather(
            self.collect_nomad_metrics(),
            self.collect_resource_metrics(),
            self.collect_dwelling_metrics(),
            self.collect_pvp_metrics(),
            self.collect_event_metrics(),
            return_exceptions=True
        )
        
        return {
            'nomads': results[0] if not isinstance(results[0], Exception) else {},
            'resources': results[1] if not isinstance(results[1], Exception) else {},
            'dwellings': results[2] if not isinstance(results[2], Exception) else {},
            'pvp': results[3] if not isinstance(results[3], Exception) else {},
            'events': results[4] if not isinstance(results[4], Exception) else {},
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def close(self):
        await self.client.aclose()
