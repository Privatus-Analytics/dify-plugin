from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.privatus_client import PrivatusClient, clamp_int, segment
from utils.tool_runner import invoke


class GetLiveVisitorsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from invoke(self, tool_parameters, self.run)

    def run(self, client: PrivatusClient, parameters: dict[str, Any]) -> tuple[str, Any]:
        site_id = client.resolve_site_id(parameters.get("site", ""))
        limit = clamp_int(parameters.get("limit"), 10, 1, 100)
        data = client.get(f"/sites/{segment(site_id)}/live.json", {"limit": limit})
        data.pop("countries", None)
        live = data.get("live_visitors", 0)
        pages = ", ".join(f"{p.get('value')} ({p.get('visits')})" for p in (data.get("top_pages") or [])[:5])
        summary = f"{live} visitor{'s' if live != 1 else ''} on the site right now."
        if pages:
            summary += f" Top pages in the last {data.get('window_minutes', 30)} minutes: {pages}."
        return summary, {"site_id": site_id, **data}
