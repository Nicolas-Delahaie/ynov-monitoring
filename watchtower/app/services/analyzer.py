from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from watchtower.models.metrics import GameplayMetric, PlayerActivity, EventMetric
import logging

logger = logging.getLogger(__name__)

class MetricsAnalyzer:
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_player_engagement(self, time_window: int = 3600) -> Dict:
        """Analyse l'engagement des joueurs sur une période"""
        cutoff = datetime.utcnow() - timedelta(seconds=time_window)
        
        active_players = self.db.query(PlayerActivity).filter(
            PlayerActivity.timestamp >= cutoff
        ).count()
        
        total_actions = self.db.query(GameplayMetric).filter(
            GameplayMetric.timestamp >= cutoff,
            GameplayMetric.metric_type == 'nomad_action'
        ).count()
        
        return {
            'active_players': active_players,
            'total_actions': total_actions,
            'avg_actions_per_player': total_actions / active_players if active_players > 0 else 0
        }
    
    def detect_anomalies(self) -> List[Dict]:
        """Détecte les anomalies dans les métriques"""
        anomalies = []
        
        # Vérifier l'activité anormalement basse
        recent_activity = self.analyze_player_engagement(time_window=300)
        if recent_activity['total_actions'] < 10:
            anomalies.append({
                'type': 'low_activity',
                'severity': 'warning',
                'message': f"Activité faible détectée: {recent_activity['total_actions']} actions en 5 min"
            })
        
        # Vérifier les taux d'échec élevés
        cutoff = datetime.utcnow() - timedelta(minutes=10)
        failed_actions = self.db.query(GameplayMetric).filter(
            GameplayMetric.timestamp >= cutoff,
            GameplayMetric.metadata['status'].astext == 'failed'
        ).count()
        
        total_actions = self.db.query(GameplayMetric).filter(
            GameplayMetric.timestamp >= cutoff
        ).count()
        
        if total_actions > 0:
            failure_rate = failed_actions / total_actions
            if failure_rate > 0.15:
                anomalies.append({
                    'type': 'high_failure_rate',
                    'severity': 'critical',
                    'message': f"Taux d'échec élevé: {failure_rate:.2%}"
                })
        
        return anomalies
    
    def get_top_players(self, limit: int = 10) -> List[Dict]:
        """Récupère les joueurs les plus actifs"""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        results = self.db.query(
            PlayerActivity.player_id,
            PlayerActivity.actions_count,
            PlayerActivity.dwelling_level,
            PlayerActivity.gold_amount,
            PlayerActivity.spice_amount
        ).filter(
            PlayerActivity.timestamp >= cutoff
        ).order_by(
            PlayerActivity.actions_count.desc()
        ).limit(limit).all()
        
        return [
            {
                'player_id': r.player_id,
                'actions': r.actions_count,
                'dwelling_level': r.dwelling_level,
                'resources': {
                    'gold': r.gold_amount,
                    'spice': r.spice_amount
                }
            }
            for r in results
        ]
