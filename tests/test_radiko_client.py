import pytest
import conftest as ct
from rarapla.data.radiko_client import RadikoClient

def test_get_area_id(sample_area_html: str, monkeypatch: pytest.MonkeyPatch) -> None:
    table = {'https://api.radiko.jp/apparea/area': __build_resp(sample_area_html)}
    fake = __build_session(table)
    cli = RadikoClient(session=fake)
    area = cli.get_area_id()
    assert area == 'JP12'

def test_fetch_now_programs_selects_current(station_list_xml: str, now_xml_current_hit: str, patch_radiko_client_datetime: bool) -> None:
    table = {'https://radiko.jp/v2/station/list/JP12.xml': __build_resp(station_list_xml), 'http://radiko.jp/v3/program/now/JP12.xml': __build_resp(now_xml_current_hit)}
    cli = RadikoClient(session=__build_session(table))
    channels = cli.fetch_now_programs('JP12')
    assert len(channels) == 2
    fmt = [c for c in channels if c.id == 'FMT'][0]
    assert fmt.program_title == 'NOW-HIT'
    assert fmt.logo_url == 'http://cdn/logo_fmt_med.png'
    tbs = [c for c in channels if c.id == 'TBS'][0]
    assert tbs.program_title == 'TBS-NOW'
    assert tbs.logo_url == 'http://cdn/logo_tbs_large.png'

def test_fetch_program_detail_date_preferred(date_xml_has_now: str, patch_radiko_client_datetime: bool) -> None:
    station = 'FMT'
    ymd = '20250102'
    table = {f'https://radiko.jp/v3/program/station/date/{ymd}/{station}.xml': __build_resp(date_xml_has_now)}
    cli = RadikoClient(session=__build_session(table))
    prog = cli.fetch_program_detail(station)
    assert prog is not None
    assert prog.title == 'DateAPI Program'
    assert prog.image == 'http://img/date.png'

def test_fetch_program_detail_weekly_fallback(weekly_xml_fallback: str, patch_radiko_client_datetime: bool) -> None:
    station = 'FMT'
    ymd = '20250102'
    table = {f'https://radiko.jp/v3/program/station/date/{ymd}/{station}.xml': __build_resp('', status=404), f'https://radiko.jp/v3/program/station/weekly/{station}.xml': __build_resp(weekly_xml_fallback)}
    cli = RadikoClient(session=__build_session(table))
    prog = cli.fetch_program_detail(station)
    assert prog is not None
    assert prog.title == 'WeeklyAPI Program'
    assert prog.pfm == 'Cさん'
    assert prog.image == 'http://img/weekly.png'

def __build_session(table: dict[str, ct.FakeResponse]) -> ct.FakeRequestsSession:
    return ct.FakeRequestsSession(table)

def __build_resp(text: str, status: int=200) -> ct.FakeResponse:
    return ct.FakeResponse(status, text)
