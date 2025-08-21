import requests
from rarapla.models.channel import Channel

class RadioBrowserClient:

    def __init__(self, base: str | None=None, session: requests.Session | None=None) -> None:
        self.base: str = base or 'https://de1.api.radio-browser.info'
        self.s: requests.Session = session or requests.Session()
        self.s.headers.update({'User-Agent': 'rapla/0.1.0'})

    def search_japan(self, limit: int=100) -> list[Channel]:
        params = {'countrycode': 'JP', 'hidebroken': 'true', 'order': 'clickcount', 'reverse': 'true', 'limit': str(limit)}
        return self._search(params)

    def search_by_tag(self, tag: str, limit: int=50) -> list[Channel]:
        params = {'tag': tag, 'hidebroken': 'true', 'order': 'clickcount', 'reverse': 'true', 'limit': str(limit)}
        return self._search(params)

    def notify_click(self, station_uuid: str) -> None:
        url = f'{self.base}/json/url/{station_uuid}'
        try:
            self.s.get(url, timeout=5)
        except Exception:
            pass

    def _search(self, params: dict[str, str]) -> list[Channel]:
        url = f'{self.base}/json/stations/search'
        r = self.s.get(url, params=params, timeout=10)
        r.raise_for_status()
        items = r.json() or []
        out: list[Channel] = []
        for it in items:
            uuid = (it.get('stationuuid') or '').strip()
            name = (it.get('name') or '').strip()
            fav = (it.get('favicon') or '').strip() or None
            stream = (it.get('url_resolved') or it.get('url') or '').strip()
            if uuid and name and stream:
                out.append(Channel(id=f'rb:{uuid}', name=name, logo_url=fav, program_title='', program_image=None, stream_url=stream))
        return out
