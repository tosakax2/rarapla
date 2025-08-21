import pytest
import rarapla.data.radiko_resolver as rr
from rarapla.data.radiko_resolver import RadikoResolver

class _FakeStream:

    def __init__(self, url: str) -> None:
        self._url = url

    def to_url(self) -> str:
        return self._url

class _FakeStreamlink:

    def __init__(self) -> None:
        self.http = _FakeHTTP()

    def set_option(self, *args: object, **kwargs: object) -> None:
        pass

    def streams(self, url: str) -> dict[str, _FakeStream]:
        return {'best': _FakeStream('https://cdn/x/master.m3u8')}

class _FakeHTTP:

    def __init__(self) -> None:
        self.headers = {'User-Agent': 'UA'}

def test_resolve_live_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rr, 'Streamlink', _FakeStreamlink)
    r = RadikoResolver()
    res = r.resolve_live('FMT')
    assert res is not None
    assert res.station_id == 'FMT'
    assert res.m3u8_url.endswith('/master.m3u8')

def test_resolve_live_none(monkeypatch: pytest.MonkeyPatch) -> None:

    class _NoBest(_FakeStreamlink):

        def streams(self, url: str) -> dict[str, _FakeStream]:
            return {}
    monkeypatch.setattr(rr, 'Streamlink', _NoBest)
    r = RadikoResolver()
    res = r.resolve_live('FMT')
    assert res is None
