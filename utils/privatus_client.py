"""A small client for the Privatus Analytics REST API.

Every request goes to https://privatusanalytics.com with the API token as a
bearer token. Nothing is stored or logged here.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote

import requests

BASE_URL = "https://privatusanalytics.com"
TIMEOUT_SECONDS = 30
USER_AGENT = "privatus-analytics-dify-plugin/0.0.1"

PERIODS = (
    "today", "yesterday", "24h", "7d", "14d", "28d", "30d", "90d", "mtd",
    "last_month", "qtd", "last_quarter", "ytd", "12mo", "last_year", "all", "custom",
)


class PrivatusError(Exception):
    """An error with a message that is safe to show to the user."""


class PrivatusClient:
    def __init__(self, api_token: str, session: requests.Session | None = None):
        token = (api_token or "").strip()
        if not token:
            raise PrivatusError("Add your Privatus Analytics API token first.")
        self._token = token
        self._session = session or requests.Session()

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        clean = {k: v for k, v in (params or {}).items() if v not in (None, "")}
        try:
            response = self._session.get(
                f"{BASE_URL}{path}",
                params=clean,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Accept": "application/json",
                    "User-Agent": USER_AGENT,
                },
                timeout=TIMEOUT_SECONDS,
            )
        except requests.RequestException as err:
            raise PrivatusError(f"Could not reach Privatus Analytics: {type(err).__name__}") from None

        try:
            body = response.json()
        except ValueError:
            body = None

        if response.status_code >= 400:
            message = None
            if isinstance(body, dict) and isinstance(body.get("error"), dict):
                message = body["error"].get("message")
            raise PrivatusError(
                f"Privatus Analytics returned {response.status_code}: {message or response.reason}"
            )
        if isinstance(body, dict) and "data" in body:
            return body["data"]
        return body

    # Workspaces and sites

    def workspace_id(self) -> str:
        workspaces = self.get("/workspaces.json")
        if not workspaces:
            raise PrivatusError("This API token cannot see any workspace.")
        return workspaces[0]["id"]

    def list_sites(self) -> list[dict[str, Any]]:
        workspace = self.workspace_id()
        sites: list[dict[str, Any]] = []
        page = 1
        while page <= 20:
            batch = self.get(
                f"/workspaces/{segment(workspace)}/sites.json",
                {"page": page, "per_page": 100},
            )
            if not batch:
                break
            sites.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return sites

    def resolve_site_id(self, site: str) -> str:
        """Takes a site ID (pa_...) or a domain like example.com."""
        value = (site or "").strip()
        if not value:
            raise PrivatusError("Say which site: a site ID like pa_7Q2K9XH3AB or a domain like example.com.")
        if value.startswith("pa_"):
            return value
        domain = normalize_domain(value)
        for item in self.list_sites():
            if normalize_domain(item.get("domain") or "") == domain:
                return item["id"]
        raise PrivatusError(f"No site with the domain {domain} was found. Use List Sites to see your sites.")


def segment(value: str) -> str:
    return quote(str(value), safe="")


def normalize_domain(value: str) -> str:
    domain = value.strip().lower()
    for prefix in ("https://", "http://"):
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.split("/")[0]
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def period_params(parameters: dict[str, Any]) -> dict[str, Any]:
    """period, from and to as the API wants them."""
    period = (parameters.get("period") or "30d").strip()
    if period not in PERIODS:
        raise PrivatusError(f"Unknown period {period}. Use one of: {', '.join(PERIODS)}.")
    params: dict[str, Any] = {"period": period}
    if period == "custom":
        start = (parameters.get("date_from") or "").strip()
        end = (parameters.get("date_to") or "").strip()
        if not start or not end:
            raise PrivatusError("A custom period needs both a start date and an end date (YYYY-MM-DD).")
        params["from"] = start
        params["to"] = end
    return params


def clamp_int(value: Any, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def period_label(period: dict[str, Any] | None) -> str:
    """'2026-10-01 to 2026-10-07' from the API period, whose end is exclusive."""
    if not period:
        return ""
    start, end = str(period.get("from", "")), str(period.get("to", ""))
    try:
        end_at = datetime.fromisoformat(end)
        if (end_at.hour, end_at.minute, end_at.second) == (0, 0, 0):
            end_at -= timedelta(days=1)
        end = end_at.date().isoformat()
    except ValueError:
        end = end[:10]
    return f"{start[:10]} to {end}"
