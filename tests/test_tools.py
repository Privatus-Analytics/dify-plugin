"""Unit tests with a fake HTTP session: no network, no token."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dify_plugin import Tool  # noqa: E402
from dify_plugin.core.utils.class_loader import load_single_subclass_from_source  # noqa: E402

from utils.privatus_client import PrivatusClient, PrivatusError, normalize_domain, period_label, period_params  # noqa: E402


class FakeResponse:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body
        self.reason = "Error"

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        path = url.replace("https://privatusanalytics.com", "")
        status, body = self.routes.get(path, (404, {"error": {"code": "not_found", "message": "We couldn't find that."}}))
        return FakeResponse(status, body)


SITES = {"data": [{"id": "pa_AAA", "domain": "example.com", "name": "Example"}, {"id": "pa_BBB", "domain": "shop.example.org", "name": "Shop"}]}
ROUTES = {
    "/workspaces.json": (200, {"data": [{"id": "ws_1"}]}),
    "/workspaces/ws_1/sites.json": (200, SITES),
    "/sites/pa_AAA/stats/aggregate.json": (200, {"data": {"period": {"from": "2026-10-01T00:00:00+00:00", "to": "2026-10-08T00:00:00+00:00"}, "metrics": {"visitors": 10, "visits": 12, "pageviews": 30, "bounce_rate": 40.0}, "change": {"visitors": 25.0, "visits": None}}}),
}


def test_sends_bearer_token_and_timeout():
    session = FakeSession(ROUTES)
    PrivatusClient("pat_x", session=session).workspace_id()
    call = session.calls[0]
    assert call["headers"]["Authorization"] == "Bearer pat_x"
    assert call["timeout"] == 30


def test_empty_token_is_refused():
    with pytest.raises(PrivatusError):
        PrivatusClient("  ")


def test_error_message_has_no_token():
    session = FakeSession({"/workspaces.json": (401, {"error": {"message": "That API token is invalid, revoked or expired."}})})
    with pytest.raises(PrivatusError) as err:
        PrivatusClient("pat_secret", session=session).workspace_id()
    assert "pat_secret" not in str(err.value)
    assert "401" in str(err.value)


def test_resolves_domain_to_site_id():
    client = PrivatusClient("pat_x", session=FakeSession(ROUTES))
    assert client.resolve_site_id("https://www.Example.com/pricing") == "pa_AAA"
    assert client.resolve_site_id("pa_ZZZ") == "pa_ZZZ"
    with pytest.raises(PrivatusError):
        client.resolve_site_id("missing.com")


def test_period_params():
    assert period_params({}) == {"period": "30d"}
    assert period_params({"period": "custom", "date_from": "2026-01-01", "date_to": "2026-01-31"}) == {"period": "custom", "from": "2026-01-01", "to": "2026-01-31"}
    with pytest.raises(PrivatusError):
        period_params({"period": "custom"})
    with pytest.raises(PrivatusError):
        period_params({"period": "forever"})


def test_helpers():
    assert normalize_domain("HTTP://www.a.com/x") == "a.com"
    assert period_label({"from": "2026-10-01T00:00:00+08:00", "to": "2026-10-08T00:00:00+08:00"}) == "2026-10-01 to 2026-10-07"


def test_get_stats_tool(monkeypatch):
    session = FakeSession(ROUTES)
    import utils.privatus_client as client_module

    monkeypatch.setattr(client_module.requests, "Session", lambda: session)
    cls = load_single_subclass_from_source(module_name="tools.get_stats", script_path=str(ROOT / "tools/get_stats.py"), parent_type=Tool)
    messages = list(cls.from_credentials({"api_token": "pat_x"})._invoke({"site": "example.com", "period": "7d"}))
    assert [m.type.value for m in messages] == ["text", "json"]
    assert messages[0].message.text == "2026-10-01 to 2026-10-07: 10 visitors (+25.0%), 12 visits, 30 pageviews, bounce rate 40.0%."
    assert session.calls[-1]["params"] == {"period": "7d", "compare": "previous_period"}


def test_every_tool_yaml_points_at_one_tool_class():
    import yaml

    provider = yaml.safe_load((ROOT / "provider/privatus_analytics.yaml").read_text())
    assert len(provider["tools"]) == 6
    for rel in provider["tools"]:
        spec = yaml.safe_load((ROOT / rel).read_text())
        source = spec["extra"]["python"]["source"]
        load_single_subclass_from_source(module_name=source[:-3].replace("/", "."), script_path=str(ROOT / source), parent_type=Tool)
