from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.collector import GameplayCollector
from app.services.analyzer import MetricsAnalyzer
from app.models.metrics import MetricResponse, DashboardStats
from app.db import get_db

router = APIRouter()
collector = GameplayCollector()

@router.get("/metrics/current", response_model=Dict)
async def get_current_metrics():
    """Récupère les métriques actuelles"""
    metrics = await collector.collect_all_metrics()
    
    # Vérifier si la collecte a réussi
    if metrics.get("status") == "error":
        raise HTTPException(status_code=503, detail="Failed to collect metrics")
    
    return metrics

@router.get("/metrics/nomads")
async def get_nomad_metrics():
    """Métriques spécifiques aux Nomads"""
    result = await collector.collect_nomad_metrics()
    
    if result.get("status") == "error":
        raise HTTPException(status_code=503, detail=result.get("message", "Unknown error"))
    
    return result

@router.get("/metrics/resources")
async def get_resource_metrics():
    """Métriques de ressources"""
    result = await collector.collect_resource_metrics()
    
    if result.get("status") == "error":
        raise HTTPException(status_code=503, detail=result.get("message", "Unknown error"))
    
    return result

@router.get("/metrics/dwellings")
async def get_dwelling_metrics():
    """Métriques des Dwellings"""
    result = await collector.collect_dwelling_metrics()
    
    if result.get("status") == "error":
        raise HTTPException(status_code=503, detail=result.get("message", "Unknown error"))
    
    return result

@router.get("/metrics/pvp")
async def get_pvp_metrics():
    """Métriques PvP"""
    result = await collector.collect_pvp_metrics()
    
    if result.get("status") == "error":
        raise HTTPException(status_code=503, detail=result.get("message", "Unknown error"))
    
    return result

@router.get("/metrics/events")
async def get_event_metrics():
    """Métriques des événements de jeu"""
    result = await collector.collect_event_metrics()
    
    if result.get("status") == "error":
        raise HTTPException(status_code=503, detail=result.get("message", "Unknown error"))
    
    return result

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    time_window: int = 3600,
    db: Session = Depends(get_db)
):
    """Statistiques pour le dashboard"""
    try:
        analyzer = MetricsAnalyzer(db)
        
        # Analyser l'engagement des joueurs
        engagement = analyzer.analyze_player_engagement(time_window)
        
        # Obtenir les joueurs les plus actifs
        top_players = analyzer.get_top_players(limit=10)
        
        return DashboardStats(
            active_players=engagement.get('active_players', 0),
            total_actions=engagement.get('total_actions', 0),
            avg_actions_per_player=engagement.get('avg_actions_per_player', 0),
            top_players=top_players,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard stats: {str(e)}")

@router.get("/alerts")
async def get_alerts(db: Session = Depends(get_db)):
    """Récupère les alertes actives"""
    try:
        analyzer = MetricsAnalyzer(db)
        
        # Détecter les anomalies
        anomalies = analyzer.detect_anomalies()
        
        # Formater les alertes
        alerts = []
        for anomaly in anomalies:
            alerts.append({
                "type": anomaly.get('type'),
                "severity": anomaly.get('severity', 'warning'),
                "message": anomaly.get('message'),
                "value": anomaly.get('value'),
                "threshold": anomaly.get('threshold'),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return {
            "total_alerts": len(alerts),
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")

@router.post("/metrics/collect")
async def trigger_collection():
    """Déclenche manuellement une collecte de métriques"""
    try:
        metrics = await collector.collect_all_metrics()
        return {
            "status": "success",
            "message": "Metrics collection triggered",
            "data": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collection failed: {str(e)}")
