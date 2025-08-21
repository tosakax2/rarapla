import asyncio
from collections.abc import Coroutine, Mapping
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Any, TypeVar
import pytest

class FakeResponse:

    def __init__(self, status_code: int=200, text: str='') -> None:
        self.status_code = status_code
        self.text = text

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f'{self.status_code}')

class FakeRequestsSession:

    def __init__(self, table: Mapping[str, FakeResponse]) -> None:
        self._table = dict(table)
        self.headers: dict[str, str] = {}

    def get(self, url: str, timeout: float | None=None) -> FakeResponse:
        resp = self._table.get(url)
        if resp is None:
            return FakeResponse(404, '')
        return resp

class _FakeAiohttpResp:

    def __init__(self, status: int=200, text: str='') -> None:
        self.status = status
        self._text = text
        self.headers = {'Content-Type': 'application/vnd.apple.mpegurl'}

    async def __aenter__(self) -> '_FakeAiohttpResp':
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any) -> bool:
        return False

    async def text(self) -> str:
        return self._text

class FakeAiohttpSession:

    def __init__(self, text: str='') -> None:
        self._text = text

    def get(self, url: str, timeout: float | None=None) -> _FakeAiohttpResp:
        return _FakeAiohttpResp(200, self._text)

@pytest.fixture
def sample_area_html() -> str:
    return '<html><div class="JP12">Chiba</div></html>'

@pytest.fixture
def station_list_xml() -> str:
    return '<?xml version="1.0" encoding="UTF-8"?>\n<stations>\n  <station>\n    <id>FMT</id>\n    <name>FM TOKYO</name>\n    <logo_medium>http://cdn/logo_fmt_med.png</logo_medium>\n    <logo_small>http://cdn/logo_fmt_small.png</logo_small>\n  </station>\n  <station>\n    <id>TBS</id>\n    <name>TBS RADIO</name>\n    <logo_large>http://cdn/logo_tbs_large.png</logo_large>\n  </station>\n</stations>\n'

@pytest.fixture
def now_xml_current_hit() -> str:
    return '<?xml version="1.0" encoding="UTF-8"?>\n<radiko>\n  <station id="FMT">\n    <name>FM TOKYO</name>\n    <progs>\n      <prog ft="20250102110000" to="20250102125959">\n        <title>NOW-HIT</title>\n        <img>http://img/now_fmt.png</img>\n      </prog>\n      <prog ft="20250102130000" to="20250102135959">\n        <title>NEXT</title>\n      </prog>\n    </progs>\n  </station>\n  <station id="TBS">\n    <name>TBS RADIO</name>\n    <progs>\n      <prog ft="20250102120000" to="20250102125959">\n        <title>TBS-NOW</title>\n      </prog>\n    </progs>\n  </station>\n</radiko>\n'

@pytest.fixture
def date_xml_has_now() -> str:
    return '<?xml version="1.0" encoding="UTF-8"?>\n<root>\n  <prog ft="20250102110000" to="20250102125959">\n    <title>DateAPI Program</title>\n    <pfm>Aさん, Bさん</pfm>\n    <desc>説明テキスト</desc>\n    <img>http://img/date.png</img>\n  </prog>\n</root>\n'

@pytest.fixture
def weekly_xml_fallback() -> str:
    return '<?xml version="1.0" encoding="UTF-8"?>\n<root>\n  <date yyyymmdd="20250102">\n    <prog ft="20250102110000" to="20250102125959">\n      <title>WeeklyAPI Program</title>\n      <pfm>Cさん</pfm>\n      <desc>週次説明</desc>\n      <img>http://img/weekly.png</img>\n    </prog>\n  </date>\n</root>\n'

class FakeDateTime(datetime):

    @classmethod
    def now(cls, tz: tzinfo | None=None) -> 'FakeDateTime':
        jst = timezone(timedelta(hours=9))
        return cls(2025, 1, 2, 12, 0, 0, tzinfo=jst if tz else None)

@pytest.fixture
def patch_radiko_client_datetime(monkeypatch: pytest.MonkeyPatch) -> bool:
    import rarapla.data.radiko_client as rc
    monkeypatch.setattr(rc, 'datetime', FakeDateTime)
    return True
T = TypeVar('T')

def run(coro: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(coro)
