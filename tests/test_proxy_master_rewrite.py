import pytest
from urllib.parse import urlencode
import conftest as ct
from rarapla.proxy.radiko_proxy import RadikoProxyServer, ResolvedStream

def test_base_url() -> None:
    s = RadikoProxyServer()
    base = s._base_url('https://host/a/b/c/master.m3u8')
    assert base == 'https://host/a/b/c/'

def test_handle_master_rewrite(monkeypatch: pytest.MonkeyPatch) -> None:
    m3u8 = '\n'.join(['#EXTM3U', '#EXT-X-STREAM-INF:BANDWIDTH=128000', 'chunklist_b128000.m3u8', '#EXT-X-STREAM-INF:BANDWIDTH=256000', 'https://cdn.radiko.example/live/FMT/chunklist_b256000.m3u8', ''])
    server = RadikoProxyServer()
    server._session = ct.FakeAiohttpSession(text=m3u8)

    async def _fake_ensure(station: str) -> ResolvedStream:
        return ResolvedStream(station_id=station, m3u8_url='https://cdn.radiko.example/live/FMT/master.m3u8')
    monkeypatch.setattr(server, '_ensure_resolved', _fake_ensure)

    class _Req:

        def __init__(self, station: str) -> None:
            self.match_info = {'station': station}
    req = _Req('FMT')
    resp = ct.run(server.handle_master(req))
    assert resp.status == 200
    out = resp.text
    exp1 = '/seg.m3u8?' + urlencode({'u': 'https://cdn.radiko.example/live/FMT/chunklist_b128000.m3u8', 'station': 'FMT'})
    exp2 = '/seg.m3u8?' + urlencode({'u': 'https://cdn.radiko.example/live/FMT/chunklist_b256000.m3u8', 'station': 'FMT'})
    assert '#EXTM3U' in out
    assert exp1 in out
    assert exp2 in out
