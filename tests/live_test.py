"""Runs every tool against the live API, the way the plugin daemon loads it.

Usage: PRIVATUS_API_TOKEN=pat_... .venv/bin/python tests/live_test.py [site]
The token is read from the environment and never printed.
"""

import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dify_plugin import Tool, ToolProvider  # noqa: E402
from dify_plugin.core.utils.class_loader import load_single_subclass_from_source  # noqa: E402

TOKEN = os.environ.get("PRIVATUS_API_TOKEN", "")
SITE = sys.argv[1] if len(sys.argv) > 1 else None

CASES = {
    "list_sites": [{}],
    "get_stats": [{"period": "7d", "compare": "previous_period"}, {"period": "custom", "date_from": "2026-10-01", "date_to": "2026-10-07", "compare": "none"}],
    "get_timeseries": [{"period": "7d", "interval": "day"}],
    "get_top_values": [{"dimension": "page", "period": "30d", "limit": 5}, {"dimension": "referrer", "period": "30d", "limit": 5}, {"dimension": "country", "period": "7d", "limit": 3}, {"dimension": "goal", "period": "30d", "limit": 3}],
    "get_live_visitors": [{"limit": 3}],
    "list_goals": [{"period": "30d"}],
}


def load(kind, rel):
    return load_single_subclass_from_source(module_name=rel.replace("/", ".")[:-3], script_path=str(ROOT / rel), parent_type=kind)


def main() -> int:
    failures = 0
    provider_yaml = yaml.safe_load((ROOT / "provider/privatus_analytics.yaml").read_text())
    provider = load(ToolProvider, provider_yaml["extra"]["python"]["source"])
    provider()._validate_credentials({"api_token": TOKEN})
    print("provider: token is valid")
    try:
        provider()._validate_credentials({"api_token": "pat_invalid"})
        print("provider: FAIL, a bad token was accepted")
        failures += 1
    except Exception as err:  # noqa: BLE001
        print(f"provider: bad token refused ({type(err).__name__}: {err})")

    for rel in provider_yaml["tools"]:
        spec = yaml.safe_load((ROOT / rel).read_text())
        name = spec["identity"]["name"]
        cls = load(Tool, spec["extra"]["python"]["source"])
        for case in CASES[name]:
            params = dict(case)
            if any(p["name"] == "site" for p in spec["parameters"]):
                params["site"] = SITE or "privatusanalytics.com"
            messages = list(cls.from_credentials({"api_token": TOKEN})._invoke(params))
            kinds = [m.type.value for m in messages]
            text = messages[0].message.text if messages else ""
            ok = kinds == ["text", "json"]
            failures += 0 if ok else 1
            print(f"{'ok  ' if ok else 'FAIL'} {name} {case}: {kinds}\n     {text[:300]}")

    # Error paths
    cls = load(Tool, "tools/get_stats.py")
    for params in ({"site": "no-such-domain.example"}, {"site": "privatusanalytics.com", "period": "custom"}, {"site": "pa_DOESNOTEXIST"}):
        messages = list(cls.from_credentials({"api_token": TOKEN})._invoke(params))
        ok = [m.type.value for m in messages] == ["text"]
        failures += 0 if ok else 1
        print(f"{'ok  ' if ok else 'FAIL'} error {params}: {messages[0].message.text}")
    print(f"\n{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
