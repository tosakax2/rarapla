from PySide6.QtCore import QObject, QThread, Signal
import asyncio
import aiohttp
from collections.abc import Mapping
from urllib.parse import parse_qs, unquote_plus

from rarapla.config import (
    ICY_CONNECT_TIMEOUT_SEC,
    ICY_METADATA_BLOCK_SIZE,
    ICY_READ_TIMEOUT_SEC,
    ICY_RETRY_DELAY_SEC,
    ICY_STOP_TIMEOUT_SEC,
)


class IcyWatcher(QThread):
    metaUpdated = Signal(str, dict)
    notSupported = Signal(str)
    networkError = Signal(str)

    def __init__(
        self, url: str, user_agent: str | None = None, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._url = url
        self._user_agent = user_agent
        self._running = False
        self._last_title = ""
        self._base_meta: dict[str, str] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task[None] | None = None
        self._session: aiohttp.ClientSession | None = None
        self._resp: aiohttp.ClientResponse | None = None

    def run(self) -> None:
        self._running = True
        loop = asyncio.new_event_loop()
        self._loop = loop
        try:
            self._task = loop.create_task(self._main())
            loop.run_until_complete(self._task)
        except Exception as e:
            self.networkError.emit(f"IcyWatcher fatal: {e!r}")
        finally:
            try:
                loop.run_until_complete(self._graceful_close())
            except Exception:
                pass
            try:
                loop.close()
            except Exception:
                pass
            self._loop = None
            self._task = None

    def stop(self) -> None:
        self._running = False
        loop = self._loop
        if loop is None:
            return

        async def _cancel() -> None:
            if self._resp is not None:
                try:
                    self._resp.close()
                except Exception:
                    pass
                self._resp = None
            if self._session is not None:
                try:
                    await self._session.close()
                except Exception:
                    pass
                self._session = None
            if self._task is not None and (not self._task.done()):
                try:
                    self._task.cancel()
                except Exception:
                    pass

        try:
            fut = asyncio.run_coroutine_threadsafe(_cancel(), loop)
            try:
                fut.result(timeout=ICY_STOP_TIMEOUT_SEC)
            except Exception:
                pass
        except Exception:
            pass

    async def _main(self) -> None:
        headers = {"Icy-MetaData": "1"}
        if self._user_agent:
            headers["User-Agent"] = self._user_agent
        timeout = aiohttp.ClientTimeout(
            sock_connect=ICY_CONNECT_TIMEOUT_SEC, sock_read=None
        )
        self._session = aiohttp.ClientSession(timeout=timeout)
        try:
            while self._running:
                try:
                    async with self._session.get(self._url, headers=headers) as resp:
                        self._resp = resp
                        metaint_str = resp.headers.get(
                            "icy-metaint"
                        ) or resp.headers.get("Icy-MetaInt")
                        self._base_meta = self._extract_headers(resp.headers)
                        self.metaUpdated.emit("", dict(self._base_meta))
                        if not metaint_str:
                            self.notSupported.emit(
                                "icy-metaint header is missing (no ICY metadata)."
                            )
                            return
                        try:
                            metaint = int(metaint_str)
                            if metaint <= 0:
                                raise ValueError
                        except Exception:
                            self.notSupported.emit(
                                f"invalid icy-metaint: {metaint_str!r}"
                            )
                            return
                        reader = resp.content
                        while self._running:
                            try:
                                await asyncio.wait_for(
                                    reader.readexactly(metaint),
                                    timeout=ICY_READ_TIMEOUT_SEC,
                                )
                                length_byte = await asyncio.wait_for(
                                    reader.readexactly(1),
                                    timeout=ICY_READ_TIMEOUT_SEC,
                                )
                            except (asyncio.TimeoutError, asyncio.IncompleteReadError):
                                continue
                            block_len = length_byte[0] * ICY_METADATA_BLOCK_SIZE
                            if block_len:
                                try:
                                    block = await asyncio.wait_for(
                                        reader.readexactly(block_len),
                                        timeout=ICY_READ_TIMEOUT_SEC,
                                    )
                                except (
                                    asyncio.TimeoutError,
                                    asyncio.IncompleteReadError,
                                ):
                                    continue
                                text = self._decode(block)
                                title, meta_map = self._parse_metadata_text(text, "")
                                if title and title != self._last_title:
                                    self._last_title = title
                                    all_meta = {**self._base_meta, **meta_map}
                                    self.metaUpdated.emit(title, all_meta)
                except asyncio.CancelledError:
                    return
                except Exception as e:
                    self.networkError.emit(f"IcyWatcher: {e!r}")
                    await asyncio.sleep(ICY_RETRY_DELAY_SEC)
                finally:
                    self._resp = None
        finally:
            pass

    async def _graceful_close(self) -> None:
        if self._resp is not None:
            try:
                self._resp.close()
            except Exception:
                pass
            self._resp = None
        if self._session is not None:
            try:
                await self._session.close()
            except Exception:
                pass
            self._session = None

    def _decode(self, data: bytes) -> str:
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                return data.rstrip(b"\x00").decode(enc, errors="ignore")
            except Exception:
                pass
        return ""

    def _parse_metadata_text(
        self, text: str, station: str
    ) -> tuple[str, dict[str, str]]:
        items: dict[str, str] = {}
        for part in text.split(";"):
            part = part.strip()
            if not part or "=" not in part:
                continue
            k, v = part.split("=", 1)
            v = v.strip().strip("'").strip('"')
            items[k.strip().lower()] = v
        title = items.get("streamtitle", "").strip()
        stream_url = items.get("streamurl", "")
        meta_map: dict[str, str] = {}
        if station:
            meta_map["Station"] = station
        if title:
            meta_map["Title"] = title
        if stream_url:
            meta_map["URL"] = stream_url
            try:
                qs = parse_qs(stream_url.split("?", 1)[1])
                artist = unquote_plus(qs.get("artist", [""])[0])
                album = unquote_plus(qs.get("album", [""])[0])
                if artist:
                    meta_map["Artist"] = artist
                if album:
                    meta_map["Album"] = album
            except Exception:
                pass
        return (title, meta_map)

    def _extract_headers(self, hdr: Mapping[str, str]) -> dict[str, str]:
        return {str(k): str(v) for k, v in hdr.items()}
