import requests
from streamlink import Streamlink
from rarapla.config import USER_AGENT

class ResolvedStream:

    def __init__(self, station_id: str, m3u8_url: str) -> None:
        self.station_id: str = station_id
        self.m3u8_url: str = m3u8_url

class RadikoResolver:

    def __init__(self) -> None:
        self._session: Streamlink = Streamlink()
        self._session.set_option('http-headers', {'User-Agent': USER_AGENT})

    def resolve_live(self, station_id: str) -> ResolvedStream | None:
        url = f'https://radiko.jp/#!/live/{station_id}'
        streams = self._session.streams(url)
        stream = streams.get('best')
        if not stream:
            return None
        return ResolvedStream(station_id, stream.to_url())

    @property
    def http(self) -> requests.Session:
        return self._session.http
