from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.privatus_client import PrivatusClient, period_label, period_params, segment
from utils.tool_runner import invoke


class GetStatsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from invoke(self, tool_parameters, self.run)

    def run(self, client: PrivatusClient, parameters: dict[str, Any]) -> tuple[str, Any]:
        site_id = client.resolve_site_id(parameters.get("site", ""))
        params = period_params(parameters)
        compare = parameters.get("compare") or "previous_period"
        if compare in ("none", "previous_period", "previous_year"):
            params["compare"] = compare
        data = client.get(f"/sites/{segment(site_id)}/stats/aggregate.json", params)
        metrics = data.get("metrics") or {}
        change = data.get("change") or {}

        def part(key: str, label: str) -> str:
            text = f"{metrics.get(key, 0)} {label}"
            if change.get(key) is not None:
                text += f" ({change[key]:+}%)"
            return text

        summary = (
            f"{period_label(data.get('period'))}: "
            + ", ".join([part("visitors", "visitors"), part("visits", "visits"), part("pageviews", "pageviews")])
            + f", bounce rate {metrics.get('bounce_rate', 0)}%."
        )
        return summary, {"site_id": site_id, **data}
