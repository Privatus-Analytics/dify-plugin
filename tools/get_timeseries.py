from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.privatus_client import PrivatusClient, period_params, segment
from utils.tool_runner import invoke


class GetTimeseriesTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from invoke(self, tool_parameters, self.run)

    def run(self, client: PrivatusClient, parameters: dict[str, Any]) -> tuple[str, Any]:
        site_id = client.resolve_site_id(parameters.get("site", ""))
        params = period_params(parameters)
        interval = parameters.get("interval") or "auto"
        if interval in ("auto", "minute", "hour", "day", "week", "month", "quarter", "year"):
            params["interval"] = interval
        data = client.get(f"/sites/{segment(site_id)}/stats/timeseries.json", params)
        series = data.get("series") or []
        lines = [f"{p.get('date', '')[:16].replace('T00:00', '')}: {p.get('visitors', 0)} visitors, {p.get('pageviews', 0)} pageviews" for p in series]
        summary = f"{len(series)} points by {data.get('interval')}:\n" + "\n".join(lines)
        return summary, {"site_id": site_id, **data}
