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
# Modifier .env selon vos besoins à partir du template
cp .env.example .env

# Lancer tous les services
docker-compose up -d --build --wait

# Vérifier le statut
docker-compose ps
```

## Accès aux services

| Service         | URL                                     | Identifiants par défaut |
|-----------------|-----------------------------------------|------------------------|
| API Watchtower  | http://localhost:8000                   | -                      |
| Docs API        | http://localhost:8000/docs              | -                      |
| Grafana         | http://localhost:3000                   | admin / admin          |

## Fonctionnement

- L’API expose des endpoints pour récupérer les métriques gameplay, les stats globales, et l’état du service.
- Les métriques sont collectées périodiquement et exposées à Prometheus.
- Grafana permet de visualiser les dashboards et de configurer des alertes personnalisées.
- **Toutes les minutes, les métriques sont publiées sur le channel NATS `ccc.watchtower` au format JSON.**

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

## Cycle d'exécution

T=0s:   Scheduler déclenche collect_all_metrics()
        ↓
T=0.5s: Collector appelle l'API CCC (GET /nomads, /resources, etc.)
        ↓
T=1s:   Enregistre en DB + incrémente métriques Prometheus
        ↓
T=15s:  Prometheus scrape GET /metrics → récupère les chiffres
        ↓
T=30s:  Grafana requête Prometheus → affiche graphiques
        ↓
T=60s:  Boucle recommence