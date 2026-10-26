from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.privatus_client import PrivatusClient, PrivatusError, clamp_int, period_params, segment
from utils.tool_runner import invoke

DIMENSIONS = (
    "page", "entry_page", "exit_page", "referrer", "channel", "utm_source", "utm_medium",
    "utm_campaign", "country", "language", "device", "browser", "os", "hostname", "event", "goal",
)
COUNT_KEYS = ("visitors", "pageviews", "completions", "conversions", "visits")


class GetTopValuesTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from invoke(self, tool_parameters, self.run)

    def run(self, client: PrivatusClient, parameters: dict[str, Any]) -> tuple[str, Any]:
        dimension = (parameters.get("dimension") or "page").strip()
        if dimension not in DIMENSIONS:
            raise PrivatusError(f"Unknown report {dimension}. Use one of: {', '.join(DIMENSIONS)}.")
        site_id = client.resolve_site_id(parameters.get("site", ""))
        params = period_params(parameters)
        params["limit"] = clamp_int(parameters.get("limit"), 10, 1, 100)
        data = client.get(f"/sites/{segment(site_id)}/breakdown/{segment(dimension)}.json", params)
        rows = data.get("rows") or []
        lines = []
        for index, row in enumerate(rows, start=1):
            key = next((k for k in COUNT_KEYS if k in row), None)
            lines.append(f"{index}. {row.get('value') or '(none)'}" + (f": {row[key]} {key}" if key else ""))
        summary = f"Top {data.get('label') or dimension} ({len(rows)} rows):\n" + "\n".join(lines)
        return summary, {"site_id": site_id, **data}
