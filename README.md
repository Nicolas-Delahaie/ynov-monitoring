# The Watchtower

## Présentation

Ce projet permet de monitorer et d’analyser le gameplay du service CCC via une API FastAPI, avec stockage des métriques, alerting, et visualisation via Prometheus et Grafana. Les métriques sont également publiées toutes les minutes sur un channel NATS pour intégration temps réel.

### Architecture

- **Watchtower (API FastAPI)** : collecte et expose les métriques gameplay.
- **PostgreSQL** : stockage des données.
- **Prometheus** : collecte et agrégation des métriques exposées par l’API.
- **Grafana** : visualisation des dashboards et alertes.
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
- **Toutes les minutes, les métriques sont publiées sur le channel NATS `ccc.metrics.watchtower` au format JSON.**

## Endpoints principaux

- `GET /api/v1/metrics/current` : toutes les métriques gameplay
- `GET /api/v1/metrics/nomads` : métriques Nomads
- `GET /api/v1/metrics/resources` : ressources
- `GET /api/v1/dashboard/stats` : stats globales
- `GET /metrics` : métriques Prometheus

## Utilisation de NATS

- Les métriques sont publiées sur le channel `ccc.watchtower`.

## Exemple de JSON d'average moves et create

```json
{
  "average_moves_per_user": 14.2,
  "average_nomads_created_per_user": 3.7,
  "period": {
    "start": "2025-12-04",
    "end": "2025-12-11",
    "days": 7
  },
  "timestamp": "2025-12-11T12:34:56.789Z"
}
```

## Exemples de JSON envoyé via NATS pour la modération sur leur channel respectif

### Déplacements suspects (ccc.watchtower.suspect_moves)
```json
{
  "suspect_ids": ["user_3", "user_7", "user_12"],
  "comment": "nombre de déplacements suspects"
}
```

### Créations de nomads suspects (ccc.watchtower.suspect_nomads_created)
```json
{
  "suspect_ids": ["user_2", "user_8"],
  "comment": "nombre de créations de nomads suspects"
}
```

## Dépannage

- Pour voir les logs d’un service :  
  `docker-compose logs <service>`
- Pour redémarrer un service :  
  `docker-compose restart <service>`
- Pour réinitialiser Grafana :  
  `docker-compose down && docker volume rm ynov-monitoring_grafana_data && docker-compose up -d`
