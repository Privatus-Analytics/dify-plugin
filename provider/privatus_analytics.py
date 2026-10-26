from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from utils.privatus_client import PrivatusClient, PrivatusError


class PrivatusAnalyticsProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            PrivatusClient(credentials.get("api_token", "")).workspace_id()
        except PrivatusError as err:
            raise ToolProviderCredentialValidationError(str(err)) from None
