from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.privatus_client import PrivatusClient, period_params, segment
from utils.tool_runner import invoke

FIELDS = ("id", "name", "kind", "pattern", "event_name", "stats")


class ListGoalsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from invoke(self, tool_parameters, self.run)

    def run(self, client: PrivatusClient, parameters: dict[str, Any]) -> tuple[str, Any]:
        site_id = client.resolve_site_id(parameters.get("site", ""))
        params = period_params(parameters)
        goals: list[dict[str, Any]] = []
        for page in range(1, 11):
            batch = client.get(f"/sites/{segment(site_id)}/goals.json", {**params, "page": page, "per_page": 100})
            if not batch:
                break
            goals.extend({k: g.get(k) for k in FIELDS} for g in batch)
            if len(batch) < 100:
                break
        goals.sort(key=lambda g: (g.get("stats") or {}).get("conversions", 0), reverse=True)
        lines = []
        for goal in goals:
            stats = goal.get("stats") or {}
            lines.append(f"{goal.get('name')}: {stats.get('conversions', 0)} conversions, {stats.get('conversion_rate', 0)}% rate")
        summary = f"{len(goals)} goal{'s' if len(goals) != 1 else ''}:\n" + "\n".join(lines)
        return summary, {"site_id": site_id, "goals": goals}
