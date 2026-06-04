import os
import time
import logging
import requests
from typing import Iterator, Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://api.hubapi.com"


class HubSpotClient:
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.environ.get("HUBSPOT_ACCESS_TOKEN", "")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
        )

    def _get(self, path: str, params: Optional[dict] = None, retries: int = 3) -> dict:
        url = f"{BASE_URL}{path}"
        for attempt in range(retries):
            try:
                resp = self.session.get(url, params=params, timeout=30)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.HTTPError as e:
                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", min(2**attempt, 60)))
                    logger.warning(f"Rate limited, waiting {wait}s")
                    time.sleep(wait)
                    continue
                if attempt < retries - 1:
                    time.sleep(2**attempt)
                    continue
                raise
            except requests.exceptions.RequestException:
                if attempt < retries - 1:
                    time.sleep(2**attempt)
                    continue
                raise
        raise RuntimeError(f"Failed after {retries} retries")

    def get_contacts(
        self, limit: int = 100, after: Optional[str] = None, properties: Optional[list] = None
    ) -> dict:
        if properties is None:
            properties = [
                "email", "firstname", "lastname", "phone",
                "lifecyclestage", "hubspot_owner_id",
            ]
        params = {"limit": limit, "properties": ",".join(properties)}
        if after:
            params["after"] = after
        return self._get("/crm/v3/objects/contacts", params=params)

    def get_all_contacts(self, properties: Optional[list] = None) -> Iterator[dict]:
        after = None
        while True:
            data = self.get_contacts(limit=100, after=after, properties=properties)
            for result in data.get("results", []):
                yield result
            paging = data.get("paging")
            if not paging:
                break
            after = paging.get("next", {}).get("after")
            if not after:
                break

    def get_deals(
        self, limit: int = 100, after: Optional[str] = None, properties: Optional[list] = None
    ) -> dict:
        if properties is None:
            properties = [
                "dealname", "amount", "dealstage", "closedate",
                "hubspot_owner_id", "hs_lastmodifieddate",
            ]
        params = {"limit": limit, "properties": ",".join(properties)}
        if after:
            params["after"] = after
        return self._get("/crm/v3/objects/deals", params=params)

    def get_all_deals(self, properties: Optional[list] = None) -> Iterator[dict]:
        after = None
        while True:
            data = self.get_deals(limit=100, after=after, properties=properties)
            for result in data.get("results", []):
                yield result
            paging = data.get("paging")
            if not paging:
                break
            after = paging.get("next", {}).get("after")
            if not after:
                break

    def get_deal_associations(self, deal_id: str) -> list:
        data = self._get(f"/crm/v3/objects/deals/{deal_id}/associations/contacts")
        return data.get("results", [])

    def get_owners(self) -> list:
        data = self._get("/crm/v3/owners")
        return data.get("results", [])
