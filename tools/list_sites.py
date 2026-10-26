from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.privatus_client import PrivatusClient
from utils.tool_runner import invoke

FIELDS = ("id", "domain", "name", "timezone", "currency", "favorite", "created_at")


class ListSitesTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from invoke(self, tool_parameters, self.run)

    def run(self, client: PrivatusClient, parameters: dict[str, Any]) -> tuple[str, Any]:
        query = (parameters.get("query") or "").strip().lower()
        sites = [{k: s.get(k) for k in FIELDS if k in s} for s in client.list_sites()]
        if query:
            sites = [s for s in sites if query in (s.get("domain") or "").lower() or query in (s.get("name") or "").lower()]
        lines = [f"{s.get('domain')} ({s.get('id')})" for s in sites]
        summary = f"{len(sites)} site{'s' if len(sites) != 1 else ''}" + (": " + ", ".join(lines) if lines else "")
        return summary, {"sites": sites}
