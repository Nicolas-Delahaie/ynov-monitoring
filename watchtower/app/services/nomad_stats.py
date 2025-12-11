from typing import Dict
from datetime import datetime, timedelta
import httpx
from typing import List
import json
import logging
import asyncio
from nats.aio.client import Client as NATS


class NomadStatsService:
    _nats_client = None
    _nats_connected = False
    _nats_url = "wss://api.ccc.bzctoons.net/nats-ws"
    logger = logging.getLogger(__name__)

    async def connect_nats(self):
        if not self._nats_client:
            self._nats_client = NATS()
        if not self._nats_connected:
            await self._nats_client.connect(servers=[self._nats_url])
            self._nats_connected = True
            self.logger.info("NATS client connected (NomadStatsService)")

    async def close_nats(self):
        if self._nats_client and self._nats_connected:
            await self._nats_client.close()
            self._nats_connected = False
            self.logger.info("NATS client closed (NomadStatsService)")

    def get_mock_daily_login_counts(self, period_days: int = 7) -> Dict[str, int]:
        """
        Mock : Retourne un nombre aléatoire de joueurs connectés par jour sur la période donnée.
        """
        end = datetime.utcnow()
        start = end - timedelta(days=period_days)
        result = {}
        for i in range(period_days):
            day = (start + timedelta(days=i)).strftime('%Y-%m-%d')
            # Mock : entre 10 et 50 joueurs connectés
            result[day] = 10 + (i * 5) % 40
        return result

    async def get_connected_user_ids(self, api_url: str, api_keys: List[str]) -> List[str]:
        """
        Utilise la route /me pour récupérer la liste des IDs des utilisateurs connectés
        à partir d'une liste de tokens actifs.
        """
        user_ids = []
        async with httpx.AsyncClient(base_url=api_url) as client:
            for token in api_keys:
                headers = {"X-Api-Key": token}
                resp = await client.get("/me", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    user_id = data.get("id")
                    if user_id:
                        user_ids.append(user_id)
        return user_ids

    async def get_nomads_move_count_today(self, api_url: str, api_key: str) -> int:
        """
        Mock : Retourne le nombre total d'appels à /nomads/move dans la journée.
        En vrai, il faudrait un endpoint d'audit/statistiques ou des logs backend.
        """
        # Ici, on simule la valeur (ex : 120 appels aujourd'hui)
        return 120

    async def get_avg_nomads_move_per_connected_user(self, api_url: str, api_keys: List[str]) -> float:
        """
        Calcule la moyenne d'appels à /nomads/move par joueur connecté aujourd'hui.
        """
        total_moves = await self.get_nomads_move_count_today(api_url, api_keys[0])
        user_ids = await self.get_connected_user_ids(api_url, api_keys)
        num_users = len(user_ids)
        if num_users == 0:
            return 0.0
        return round(total_moves / num_users, 2)

    def get_mock_moves_per_user(self, user_ids: List[str]) -> Dict[str, int]:
        """
        Mock : Retourne un nombre simulé de moves pour chaque utilisateur.
        """
        # Génère un nombre de moves aléatoire pour chaque utilisateur
        return {user_id: 10 + idx * 3 for idx, user_id in enumerate(user_ids)}

    def users_above_global_average(self, user_ids: List[str], global_avg: float) -> List[str]:
        """
        Retourne la liste des IDs des utilisateurs qui dépassent la moyenne globale de moves.
        """
        moves_per_user = self.get_mock_moves_per_user(user_ids)
        return [user_id for user_id, moves in moves_per_user.items() if moves > global_avg]

    def top_5_percent_above_average(self, user_ids: List[str], global_avg: float) -> List[str]:
        """
        Retourne la liste des IDs des 5% de joueurs qui dépassent le plus la moyenne globale de moves.
        """
        moves_per_user = self.get_mock_moves_per_user(user_ids)
        # Filtrer ceux qui dépassent la moyenne
        above_avg = [(user_id, moves) for user_id, moves in moves_per_user.items() if moves > global_avg]
        # Trier par moves décroissant
        above_avg.sort(key=lambda x: x[1], reverse=True)
        # Garder les 5% les plus hauts
        n = max(1, int(len(above_avg) * 0.05))
        return [user_id for user_id, _ in above_avg[:n]]

    async def send_suspect_move_ids_nats(self, user_ids: List[str]):
        """
        Envoie les IDs des joueurs suspects via NATS avec le commentaire demandé.
        """
        message = {
            "suspect_ids": user_ids,
            "comment": "nombre de déplacements suspects"
        }
        await self.connect_nats()
        if self._nats_client.is_connected:
            await self._nats_client.publish("ccc.watchtower.suspect_moves", json.dumps(message).encode())
        self.logger.info(f"Sent suspect moves IDs via NATS: {message}")


    def get_mock_nomads_created_per_user(self, user_ids: List[str]) -> Dict[str, int]:
        """
        Mock : Retourne un nombre simulé de nomads créés pour chaque utilisateur.
        """
        # Génère un nombre de créations aléatoire pour chaque utilisateur
        return {user_id: 2 + idx for idx, user_id in enumerate(user_ids)}

    def users_above_global_created_average(self, user_ids: List[str], global_avg: float) -> List[str]:
        """
        Retourne la liste des IDs des utilisateurs qui dépassent la moyenne globale de nomads créés.
        """
        created_per_user = self.get_mock_nomads_created_per_user(user_ids)
        return [user_id for user_id, created in created_per_user.items() if created > global_avg]

    def top_5_percent_above_created_average(self, user_ids: List[str], global_avg: float) -> List[str]:
        """
        Retourne la liste des IDs des 5% de joueurs qui dépassent le plus la moyenne globale de nomads créés.
        """
        created_per_user = self.get_mock_nomads_created_per_user(user_ids)
        above_avg = [(user_id, created) for user_id, created in created_per_user.items() if created > global_avg]
        above_avg.sort(key=lambda x: x[1], reverse=True)
        n = max(1, int(len(above_avg) * 0.05))
        return [user_id for user_id, _ in above_avg[:n]]

    async def send_suspect_created_ids_nats(self, user_ids: List[str]):
        """
        Envoie les IDs des joueurs suspects via NATS avec le commentaire pour créations.
        """
        message = {
            "suspect_ids": user_ids,
            "comment": "nombre de créations de nomads suspects"
        }
        await self.connect_nats()
        if self._nats_client.is_connected:
            await self._nats_client.publish("ccc.watchtower.suspect_nomads_created", json.dumps(message).encode())
        self.logger.info(f"Sent suspect created IDs via NATS: {message}")

    def get_suspect_moves_json(self, user_ids: List[str]) -> Dict:
        """
        Retourne le JSON des déplacements suspects pour les IDs fournis.
        """
        return {
            "suspect_ids": user_ids,
            "comment": "nombre de déplacements suspects"
        }

    def get_suspect_created_json(self, user_ids: List[str]) -> Dict:
        """
        Retourne le JSON des créations de nomads suspects pour les IDs fournis.
        """
        return {
            "suspect_ids": user_ids,
            "comment": "nombre de créations de nomads suspects"
        }

    def get_average_moves_and_create_json(self, average_moves: float, average_create: float, start: str, end: str, days: int) -> Dict:
        """
        Retourne le JSON d'average pour les moves et create sur une période donnée.
        """
        return {
            "average_moves_per_user": round(average_moves, 2),
            "average_nomads_created_per_user": round(average_create, 2),
            "period": {
                "start": start,
                "end": end,
                "days": days
            },
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }

