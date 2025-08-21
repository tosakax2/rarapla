"""Client for the Radio Browser API."""

import requests
from rarapla.models.channel import Channel


class RadioBrowserClient:
    """Query stations from the community Radio Browser service."""

    def __init__(
        self, base: str | None = None, session: requests.Session | None = None
    ) -> None:
        """Initialize the client.

        Args:
            base: Base URL of the Radio Browser API.
            session: Optional requests session to reuse.
        """
        self.base: str = base or "https://de1.api.radio-browser.info"
        self.s: requests.Session = session or requests.Session()
        self.s.headers.update({"User-Agent": "rapla/0.1.0"})

    def search_japan(self, limit: int = 100) -> list[Channel]:
        """Search for popular Japanese stations.

        Args:
            limit: Maximum number of results to return.

        Returns:
            List of matching channels.
        """
        params = {
            "countrycode": "JP",
            "hidebroken": "true",
            "order": "clickcount",
            "reverse": "true",
            "limit": str(limit),
        }
        return self._search(params)

    def search_by_tag(self, tag: str, limit: int = 50) -> list[Channel]:
        """Search stations by a tag.

        Args:
            tag: Tag name to filter by.
            limit: Maximum number of results to return.

        Returns:
            List of matching channels.
        """
        params = {
            "tag": tag,
            "hidebroken": "true",
            "order": "clickcount",
            "reverse": "true",
            "limit": str(limit),
        }
        return self._search(params)

    def notify_click(self, station_uuid: str) -> None:
        """Notify the API that a station has been clicked.

        Failures are ignored as the call is best-effort.

        Args:
            station_uuid: UUID of the station.
        """
        url = f"{self.base}/json/url/{station_uuid}"
        try:
            self.s.get(url, timeout=5)
        except Exception:
            pass

    def _search(self, params: dict[str, str]) -> list[Channel]:
        """Perform a search request against the API."""
        url = f"{self.base}/json/stations/search"
        r = self.s.get(url, params=params, timeout=10)
        r.raise_for_status()
        items = r.json() or []
        out: list[Channel] = []
        for it in items:
            uuid = (it.get("stationuuid") or "").strip()
            name = (it.get("name") or "").strip()
            fav = (it.get("favicon") or "").strip() or None
            stream = (it.get("url_resolved") or it.get("url") or "").strip()
            if uuid and name and stream:
                out.append(
                    Channel(
                        id=f"rb:{uuid}",
                        name=name,
                        logo_url=fav,
                        program_title="",
                        program_image=None,
                        stream_url=stream,
                    )
                )
        return out
