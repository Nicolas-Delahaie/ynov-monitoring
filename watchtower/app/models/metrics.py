from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict

Base = declarative_base()

class GameplayMetric(Base):
    __tablename__ = "gameplay_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metric_type = Column(String, index=True)  # nomad_action, resource, event, pvp
    metric_name = Column(String, index=True)
    value = Column(Float)
    extra_data = Column(JSON)
    player_id = Column(String, index=True, nullable=True)
    clan_id = Column(String, index=True, nullable=True)

class PlayerActivity(Base):
    __tablename__ = "player_activity"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    player_id = Column(String, index=True)
    dwelling_level = Column(Integer)
    active_nomads = Column(Integer)
    gold_amount = Column(Float)
    spice_amount = Column(Float)
    actions_count = Column(Integer)
    exploration_radius = Column(Float)

class EventMetric(Base):
    __tablename__ = "event_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String, index=True)  # tempete, raid, benediction, faille
    affected_players = Column(Integer)
    impact_score = Column(Float)
    extra_data = Column(JSON)

# Pydantic models pour l'API
class MetricResponse(BaseModel):
    metric_type: str
    metric_name: str
    value: float
    timestamp: datetime
    metadata: Optional[Dict] = None

class DashboardStats(BaseModel):
    total_actions: int
    active_players: int
    resources_collected: Dict[str, float]
    top_events: list
    pvp_activity: Dict[str, int]
