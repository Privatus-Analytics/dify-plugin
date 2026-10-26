from collections.abc import Callable, Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.privatus_client import PrivatusClient, PrivatusError

Runner = Callable[[PrivatusClient, dict[str, Any]], tuple[str, Any]]


def invoke(tool: Tool, parameters: dict[str, Any], run: Runner) -> Generator[ToolInvokeMessage, None, None]:
    """Runs `run` and yields a short text summary and the JSON result.

    Errors are shown as a plain message, never with the token.
    """
    try:
        client = PrivatusClient(tool.runtime.credentials.get("api_token", ""))
        summary, data = run(client, parameters)
    except PrivatusError as err:
        yield tool.create_text_message(str(err))
        return
    yield tool.create_text_message(summary)
    yield tool.create_json_message(data if isinstance(data, dict) else {"items": data})
