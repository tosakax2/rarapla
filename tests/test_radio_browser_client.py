import pytest
from rarapla.data.radio_browser_client import RadioBrowserClient
from rarapla.models.channel import Channel


class DummyResp:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(self.status_code)

    def json(self):
        return self._json


class DummySession:
    def __init__(self, json_data):
        self.json_data = json_data
        self.last_url = None
        self.last_params: dict[str, str] | None = None
        self.headers: dict[str, str] = {}

    def get(self, url: str, params: dict[str, str] | None = None, timeout: float | None = None):
        self.last_url = url
        self.last_params = params
        return DummyResp(self.json_data)


def test_search_japan_parses_response() -> None:
    data = [
        {
            "stationuuid": "abcd",
            "name": "Test Station",
            "favicon": "http://logo.png",
            "url_resolved": "http://stream",
        },
        {
            "stationuuid": "",  # invalid item should be ignored
        },
    ]
    sess = DummySession(data)
    cli = RadioBrowserClient(base="http://api", session=sess)
    channels = cli.search_japan(limit=2)
    assert sess.last_url == "http://api/json/stations/search"
    assert sess.last_params == {
        "countrycode": "JP",
        "hidebroken": "true",
        "order": "clickcount",
        "reverse": "true",
        "limit": "2",
    }
    assert len(channels) == 1
    ch = channels[0]
    assert isinstance(ch, Channel)
    assert ch.id == "rb:abcd"
    assert ch.name == "Test Station"
    assert ch.logo_url == "http://logo.png"
    assert ch.stream_url == "http://stream"


def test_search_by_tag_builds_params(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, dict[str, str]] = {}

    def fake_search(self, params: dict[str, str]):
        captured["params"] = params
        return []

    monkeypatch.setattr(RadioBrowserClient, "_search", fake_search, raising=False)
    cli = RadioBrowserClient()
    cli.search_by_tag("rock", limit=33)
    assert captured["params"] == {
        "tag": "rock",
        "hidebroken": "true",
        "order": "clickcount",
        "reverse": "true",
        "limit": "33",
    }


def test_notify_click_ignores_errors() -> None:
    called = {}

    class ErrSession:
        headers: dict[str, str] = {}

        def get(self, url: str, timeout: float | None = None):
            called["url"] = url
            raise RuntimeError("boom")

    cli = RadioBrowserClient(base="http://api", session=ErrSession())
    # Should not raise even though session.get raises
    cli.notify_click("uuid123")
    assert called["url"] == "http://api/json/url/uuid123"
