"""Client for fetching program information from Radiko APIs."""

from datetime import datetime, timedelta, timezone
import re
import xml.etree.ElementTree as ET
import requests
from rarapla.config import HTTP_TIMEOUT, USER_AGENT
from rarapla.models.channel import Channel
from rarapla.models.program import Program


class RadikoClient:
    """Interact with the public Radiko HTTP APIs."""

    def __init__(self, session: requests.Session | None = None) -> None:
        """Create a new client.

        Args:
            session: Optional preconfigured requests session.
        """
        self.s: requests.Session = session or requests.Session()
        self.s.headers.update({"User-Agent": USER_AGENT})

    def get_area_id(self) -> str:
        """Return the listener's area identifier."""
        r = self.s.get("https://api.radiko.jp/apparea/area", timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        m = re.search('class="(JP\\d{2})"', r.text)
        if not m:
            raise RuntimeError("AreaId not found")
        return m.group(1)

    def _fetch_station_logos(self, area_id: str) -> dict[str, str]:
        """Fetch station logo URLs for an area."""
        url = f"https://radiko.jp/v2/station/list/{area_id}.xml"
        r = self.s.get(url, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        logos: dict[str, str] = {}
        for st in root.findall(".//station"):
            sid = (st.findtext("id") or "").strip()
            logo = (
                (st.findtext("logo_medium") or "").strip()
                or (st.findtext("logo_large") or "").strip()
                or (st.findtext("logo_small") or "").strip()
                or (st.findtext("logo_xsmall") or "").strip()
            )
            if sid and logo:
                logos[sid] = logo
        return logos

    def fetch_now_programs(self, area_id: str) -> list[Channel]:
        """Fetch currently airing programs for all stations in an area.

        Args:
            area_id: Area identifier returned from :meth:`get_area_id`.

        Returns:
            List of channels with their current program information.
        """
        logo_map = self._fetch_station_logos(area_id)
        url = f"http://radiko.jp/v3/program/now/{area_id}.xml"
        r = self.s.get(url, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        jst = timezone(timedelta(hours=9))
        now = datetime.now(jst).strftime("%Y%m%d%H%M%S")
        channels: list[Channel] = []
        for st in root.findall(".//station"):
            sid = st.get("id") or ""
            name = (st.findtext("name") or "").strip()
            progs = st.findall(".//prog")
            prog_node = None
            for p in progs:
                ft = (p.get("ft") or "").strip()
                to = (p.get("to") or "").strip()
                if ft and to and (ft <= now <= to):
                    prog_node = p
                    break
            if prog_node is None and progs:
                prog_node = progs[0]
            title = ""
            img = None
            if prog_node is not None:
                title = (prog_node.findtext("title") or "").strip()
                img = prog_node.findtext("img") or None
            logo = logo_map.get(sid)
            if not logo and sid:
                logo = f"http://radiko.jp/station/logo/{sid}/logo_small.png"
            channels.append(Channel(sid, name, logo, title, img))
        return channels

    def fetch_program_detail(self, station_id: str) -> Program | None:
        """Fetch detailed information about the program currently airing.

        Args:
            station_id: Station identifier.

        Returns:
            Program details or ``None`` if the API request fails.
        """
        jst = timezone(timedelta(hours=9))
        now = datetime.now(jst)
        ymd = now.strftime("%Y%m%d")
        now_str = now.strftime("%Y%m%d%H%M%S")
        date_url = f"https://radiko.jp/v3/program/station/date/{ymd}/{station_id}.xml"
        try:
            r = self.s.get(date_url, timeout=HTTP_TIMEOUT)
            if r.status_code == 404:
                weekly_url = (
                    f"https://radiko.jp/v3/program/station/weekly/{station_id}.xml"
                )
                rw = self.s.get(weekly_url, timeout=HTTP_TIMEOUT)
                rw.raise_for_status()
                root = ET.fromstring(rw.text)
                return self._pick_now_program_from_weekly(root, now_str, ymd)
            r.raise_for_status()
            root = ET.fromstring(r.text)
            return self._pick_now_program_from_date(root, now_str)
        except requests.RequestException:
            return None

    def _pick_now_program_from_date(
        self, root: ET.Element, now_str: str
    ) -> Program | None:
        """Pick the program matching ``now_str`` from a date XML."""
        for prog in root.findall(".//prog"):
            ft = prog.get("ft") or ""
            to = prog.get("to") or ""
            if ft <= now_str <= to:
                return self._program_from_xml(prog)
        return None

    def _pick_now_program_from_weekly(
        self, root: ET.Element, now_str: str, ymd: str
    ) -> Program | None:
        """Pick the program matching ``now_str`` from a weekly XML."""
        for day in root.findall(".//date"):
            if day.get("yyyymmdd") != ymd:
                continue
            for prog in day.findall(".//prog"):
                ft = prog.get("ft") or ""
                to = prog.get("to") or ""
                if ft <= now_str <= to:
                    return self._program_from_xml(prog)
        return None

    def _program_from_xml(self, prog: ET.Element) -> Program:
        """Create a :class:`Program` instance from an XML node."""
        return Program(
            title=(prog.findtext("title") or "").strip(),
            pfm=prog.findtext("pfm") or None,
            desc=prog.findtext("desc") or None,
            image=prog.findtext("img") or None,
        )
