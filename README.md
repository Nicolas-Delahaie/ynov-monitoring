# Ynov Monitoring - The Watchtower

## Présentation

Ce projet permet de monitorer et d’analyser le gameplay du service CCC via une API FastAPI, avec stockage des métriques, alerting, et visualisation via Prometheus et Grafana. Les métriques sont également publiées toutes les minutes sur un channel NATS pour intégration temps réel.

### Architecture

- **Watchtower (API FastAPI)** : collecte et expose les métriques gameplay.
- **PostgreSQL** : stockage des données.
- **Prometheus** : collecte et agrégation des métriques exposées par l’API.
- **Grafana** : visualisation des dashboards et alertes.
- **Redis** : cache et gestion des tâches.
- **NATS** : publication des métriques en Pub/Sub (temps réel).

## Démarrage rapide

```bash
# 1. Cloner le projet
git clone <repo-url>
cd ynov-monitoring

# 2. Configurer les variables d'environnement
cp .env.example .env
# Modifier .env selon vos besoins (API_KEY, DB, etc.)

# 3. Installer les dépendances Python
pip install -r watchtower/requirements.txt

# 4. Lancer tous les services (incluant NATS)
docker-compose up -d

# 5. Vérifier le statut
docker-compose ps
```

## Accès aux services

| Service         | URL                        | Identifiants par défaut |
|-----------------|----------------------------|------------------------|
| API Watchtower  | http://localhost:8000      | -                      |
| Docs API        | http://localhost:8000/docs | -                      |
| Prometheus      | http://localhost:9090      | -                      |
| Grafana         | http://localhost:3000      | admin / admin          |
| NATS            | nats://localhost:4222      | -                      |

## Fonctionnement

- L’API expose des endpoints pour récupérer les métriques gameplay, les stats globales, et l’état du service.
- Les métriques sont collectées périodiquement et exposées à Prometheus.
- Grafana permet de visualiser les dashboards et de configurer des alertes personnalisées.
- **Toutes les minutes, les métriques sont publiées sur le channel NATS `metrics.watchtower` au format JSON.**

## Endpoints principaux

- `GET /api/v1/metrics/current` : toutes les métriques gameplay
- `GET /api/v1/metrics/nomads` : métriques Nomads
- `GET /api/v1/metrics/resources` : ressources
- `GET /api/v1/dashboard/stats` : stats globales
- `GET /metrics` : métriques Prometheus

## Utilisation de NATS

- Les métriques sont publiées sur le channel `metrics.watchtower`.
- Pour consommer les messages, utilisez un client NATS compatible.

### Exemple de message JSON envoyé sur NATS

```json
{
  "nomads": {
    "total_nomads": 42,
    "by_action": {
      "move": 120,
      "attack": 15
    },
    "by_player": {
      "player1": {"move": 10, "attack": 2},
      "player2": {"move": 8, "attack": 1}
    }
  },
  "resources": {
    "total_gold": 5000,
    "total_spice": 1200,
    "by_player": {
      "player1": {"gold": 300, "spice": 50},
      "player2": {"gold": 250, "spice": 40}
    }
  },
  "dwellings": {
    "by_level": {"1": 10, "2": 5, "3": 2, "4": 1},
    "total": 18
  },
  "pvp": {
    "total_attacks": 20,
    "successful_attacks": 15,
    "destroyed_dwellings": 3
  },
  "events": {
    "by_type": {
      "tempete": {"count": 2, "affected_players": 5},
      "raid": {"count": 1, "affected_players": 2}
    },
    "total": 3
  },
  "timestamp": "2025-12-08T12:34:56.789Z"
}
```

## Dépannage

- Pour voir les logs d’un service :  
  `docker-compose logs <service>`
- Pour redémarrer un service :  
  `docker-compose restart <service>`
- Pour réinitialiser Grafana :  
  `docker-compose down && docker volume rm ynov-monitoring_grafana_data && docker-compose up -d`