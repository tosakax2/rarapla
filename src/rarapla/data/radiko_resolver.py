"""Resolve Radiko live stream URLs using Streamlink."""

import requests
from streamlink import Streamlink
from rarapla.config import USER_AGENT


class ResolvedStream:
    """Container for a resolved Radiko stream."""

    def __init__(self, station_id: str, m3u8_url: str) -> None:
        """Initialize the stream information.

        Args:
            station_id: Station identifier.
            m3u8_url: Direct URL to the master playlist.
        """
        self.station_id: str = station_id
        self.m3u8_url: str = m3u8_url


class RadikoResolver:
    """Resolve Radiko station IDs into playable stream URLs."""

    def __init__(self) -> None:
        """Create a new resolver with a preconfigured Streamlink session."""
        self._session: Streamlink = Streamlink()
        self._session.set_option('http-headers', {'User-Agent': USER_AGENT})

    def resolve_live(self, station_id: str) -> ResolvedStream | None:
        """Resolve the live stream for a station.

        Args:
            station_id: Station identifier.

        Returns:
            The resolved stream information or ``None`` if not available.
        """
        url = f'https://radiko.jp/#!/live/{station_id}'
        streams = self._session.streams(url)
        stream = streams.get('best')
        if not stream:
            return None
        return ResolvedStream(station_id, stream.to_url())

    @property
    def http(self) -> requests.Session:
        """Expose the underlying requests session used by Streamlink."""
        return self._session.http
