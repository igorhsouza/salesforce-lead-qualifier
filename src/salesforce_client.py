import logging
from typing import Any

import requests
from pydantic import BaseModel, Field
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("salesforce_client")


class TokenResponse(BaseModel):
    access_token: str
    instance_url: str
    token_type: str = Field(default="Bearer")


class SalesforceClient:
    def __init__(self) -> None:
        self.base_domain = str(settings.sf_domain).rstrip("/")
        self.api_version = settings.sf_api_version
        self._token: TokenResponse | None = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def authenticate(self) -> TokenResponse:
        token_url = f"{self.base_domain}/services/oauth2/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.sf_client_id,
            "client_secret": settings.sf_client_secret,
        }

        logger.info("Authenticating with Salesforce via Client Credentials...")
        response = requests.post(token_url, data=payload, timeout=15)
        response.raise_for_status()

        self._token = TokenResponse.model_validate(response.json())
        logger.info("Authentication succeeded. Instance: %s", self._token.instance_url)
        return self._token

    @property
    def _headers(self) -> dict[str, str]:
        if not self._token:
            self.authenticate()
        return {
            "Authorization": f"Bearer {self._token.access_token}",  # type: ignore[union-attr]
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def query_leads(self, limit: int = 5) -> list[dict[str, Any]]:
        if not self._token:
            self.authenticate()

        soql = f"SELECT Id, Name, Company, Email, Status, Rating, Description FROM Lead LIMIT {limit}"
        url = f"{self._token.instance_url}/services/data/{self.api_version}/query"  # type: ignore[union-attr]

        response = requests.get(url, headers=self._headers, params={"q": soql}, timeout=15)
        response.raise_for_status()

        records = response.json().get("records", [])
        logger.info("SOQL query returned %d Lead(s).", len(records))
        return records

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def update_lead(self, lead_id: str, rating: str, description: str) -> None:
        if not self._token:
            self.authenticate()

        url = f"{self._token.instance_url}/services/data/{self.api_version}/sobjects/Lead/{lead_id}"  # type: ignore[union-attr]
        body = {
            "Rating": rating,
            "Description": description,
        }

        response = requests.patch(url, headers=self._headers, json=body, timeout=15)
        response.raise_for_status()
        logger.info("Lead %s updated (Rating=%s).", lead_id, rating)


if __name__ == "__main__":
    client = SalesforceClient()
    leads = client.query_leads(limit=5)
    for lead in leads:
        print(
            f"- {lead.get('Id')} | {lead.get('Name')} | {lead.get('Company')} | Rating={lead.get('Rating')}"
        )
