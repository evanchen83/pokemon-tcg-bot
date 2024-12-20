import logging

import requests
from cachetools import TTLCache, cached

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

_cache = TTLCache(maxsize=50, ttl=3600)


class PokemonTCGAPI:
    def __init__(self, api_key: str):
        self.base_url = "https://api.pokemontcg.io/v2"
        self.headers = {"X-Api-Key": api_key}

    def _make_request(self, method: str, path: str, params: dict = None):
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = requests.request(
            method=method, url=url, headers=self.headers, params=params, timeout=10
        )
        response.raise_for_status()
        return response.json()

    @cached(cache=_cache, key=lambda self: "get_sets")
    def get_sets(self) -> list[dict]:
        params = {"select": "id,name,series,releaseDate,total"}
        response = self._make_request("GET", "/sets", params=params)
        return response.get("data", [])

    @cached(cache=_cache, key=lambda self, set_id: f"get_cards_by_set_id:{set_id}")
    def get_cards_by_set_id(self, set_id: str) -> list[dict]:
        params = {
            "q": f"set.id:{set_id}",
            "select": "id,name,rarity,types,number,images,set",
        }
        response = self._make_request("GET", "/cards", params=params)
        return response.get("data", [])

    @cached(
        cache=_cache,
        key=lambda self,
        card_ids,
        search_name: f"get_cards_by_ids:{','.join(card_ids)}:{search_name}",
    )
    def get_cards_by_ids(
        self, card_ids: list[str], search_name: str = None
    ) -> list[dict]:
        query = "(" + " OR ".join([f"id:{card_id}" for card_id in card_ids]) + ")"
        if search_name:
            query += f" name:*{search_name}*"

        params = {"q": query, "select": "id,name,rarity,types,number,images,small,set"}

        response = self._make_request("GET", "/cards", params=params)
        return response.get("data", [])

    @cached(
        cache=_cache,
        key=lambda self, query, select: f"get_cards:{query}.{select}",
    )
    def get_cards(self, query: str, select: str) -> list[dict]:
        response = self._make_request(
            "GET", "/cards", params={"q": query, "select": select, "pageSize": 30}
        )
        return response.get("data", [])
