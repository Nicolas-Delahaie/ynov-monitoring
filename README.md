# The Watchtower

## Présentation

Ce projet permet de monitorer et d’analyser le gameplay du service CCC via une API FastAPI, avec stockage des métriques, alerting, et visualisation via Prometheus et Grafana.

### Architecture

- **Watchtower (API FastAPI)** : collecte et expose les métriques gameplay.
- **PostgreSQL** : stockage des données.
- **Prometheus** : collecte et agrégation des métriques exposées par l’API.
- **Grafana** : visualisation des dashboards et alertes.

## Démarrage rapide

```bash
# 1. Cloner le projet
git clone <repo-url>
cd ynov-monitoring

# 2. Configurer les variables d'environnement
cp .env.example .env
# Modifier .env selon vos besoins (API_KEY, DB, etc.)

# 3. Lancer tous les services
docker-compose up -d

# 4. Vérifier le statut
docker-compose ps
```

## Accès aux services

| Service         | URL                        | Identifiants par défaut |
|-----------------|----------------------------|------------------------|
| API Watchtower  | http://localhost:8000      | -                      |
| Docs API        | http://localhost:8000/docs | -                      |
| Prometheus      | http://localhost:9090      | -                      |
| Grafana         | http://localhost:3000      | admin / admin          |

## Fonctionnement

- L’API expose des endpoints pour récupérer les métriques gameplay, les stats globales, et l’état du service.
- Les métriques sont collectées périodiquement et exposées à Prometheus.
- Grafana permet de visualiser les dashboards et de configurer des alertes personnalisées.

## Endpoints principaux

- `GET /api/v1/metrics/current` : toutes les métriques gameplay
- `GET /api/v1/metrics/nomads` : métriques Nomads
- `GET /api/v1/metrics/resources` : ressources
- `GET /api/v1/dashboard/stats` : stats globales
- `GET /metrics` : métriques Prometheus

## Dépannage

- Pour voir les logs d’un service :  
  `docker-compose logs <service>`
- Pour redémarrer un service :  
  `docker-compose restart <service>`
- Pour réinitialiser Grafana :  
  `docker-compose down && docker volume rm ynov-monitoring_grafana_data && docker-compose up -d`