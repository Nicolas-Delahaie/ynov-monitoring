## Démarrage et Utilisation

```bash
# Installation des dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env avec vos paramètres

# Démarrage avec Docker
docker-compose up -d

# Ou démarrage local
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

# Accès aux Services

## API Watchtower
- **URL** : http://localhost:8000

## Documentation API
- **URL** : http://localhost:8000/docs

## Métriques Prometheus
- **URL** : http://localhost:8000/metrics

## Prometheus UI
- **URL** : http://localhost:9090

## Grafana Dashboard
- **URL** : http://localhost:3000
- **Identifiants** : `admin` / `admin`