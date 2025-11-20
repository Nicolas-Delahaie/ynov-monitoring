from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from datetime import datetime, timedelta

from app.services.collector import GameplayCollector
from app.models.metrics import MetricResponse, DashboardStats

router = APIRouter()
collector = GameplayCollector()

@router.get("/metrics/current", response_model=Dict)
async def get_current_metrics():
    """Récupère les métriques actuelles"""
    metrics = await collector.collect_all_metrics()
    return metrics

@router.get("/metrics/nomads")
async def get_nomad_metrics():
    """Métriques spécifiques aux Nomads"""
    return await collector.collect_nomad_metrics()

@router.get("/metrics/resources")
async def get_resource_metrics():
    """Métriques de ressources"""
    return await collector.collect_resource_metrics()

@router.get("/metrics/dwellings")
async def get_dwelling_metrics():
    """Métriques des Dwellings"""
    return await collector.collect_dwelling_metrics()

@router.get("/metrics/pvp")
async def get_pvp_metrics():
    """Métriques PvP"""
    return await collector.collect_pvp_metrics()

@router.get("/metrics/events")
async def get_event_metrics():
    """Métriques des événements"""
    return await collector.collect_event_metrics()

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Stats globales pour le dashboard"""
    all_metrics = await collector.collect_all_metrics()
    
    return DashboardStats(
        total_actions=sum(all_metrics.get('nomads', {}).get('by_action', {}).values()),
        active_players=len(all_metrics.get('resources', {}).get('by_player', {})),
        resources_collected={
            'gold': all_metrics.get('resources', {}).get('total_gold', 0),
            'spice': all_metrics.get('resources', {}).get('total_spice', 0)
        },
        top_events=list(all_metrics.get('events', {}).get('by_type', {}).keys())[:5],
        pvp_activity=all_metrics.get('pvp', {})
    )

@router.get("/alerts")
async def get_active_alerts():
    """Liste des alertes actives"""
    # À implémenter avec la logique d'alerting
    return {"alerts": []}
