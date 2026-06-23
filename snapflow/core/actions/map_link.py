"""Open a map URL in the default browser."""

import webbrowser

from snapflow.core.actions.base import ActionError, BaseAction


class MapAction(BaseAction):
    action_type = "map"

    def execute(self, data: str) -> str:
        url = data.strip()
        if not url.startswith(("http://", "https://")):
            raise ActionError(f"Invalid map URL: {url}")
        webbrowser.open(url)
        return "Opened map in your browser."


class AddressAction(MapAction):
    action_type = "address"
