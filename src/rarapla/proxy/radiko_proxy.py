"""Lightweight proxy server that rewrites Radiko streams."""

import asyncio
import os
import threading
from urllib.parse import urlencode, urljoin, urlparse

import aiohttp
from aiohttp import web
from rarapla.config import (
    HTTP_TIMEOUT,
    RADIKO_CACHE_TTL_SEC,
    RADIKO_CHUNK_SIZE,
    RADIKO_RESOLVE_TTL_SEC,
    RADIKO_RETRY_DELAY_SEC,
    RADIKO_SEGMENT_RETRY_ATTEMPTS,
)
from rarapla.data.radiko_resolver import RadikoResolver, ResolvedStream


class RadikoProxyServer:
    """Proxy Radiko streams and rewrite playlist URLs."""

    def __init__(self, host: str = "127.0.0.1", port: int = 3032) -> None:
        """Initialize the proxy server.

        Args:
            host: Hostname to bind.
            port: TCP port to listen on.
        """
        self.host: str = host
        self.port: int = port
        self._resolver: RadikoResolver = RadikoResolver()
        self._app: web.Application = web.Application()
        self._app.add_routes(
            [
                web.get("/live/{station}.m3u8", self.handle_master),
                web.get("/seg", self.handle_seg),
                web.get("/seg.{ext}", self.handle_seg),
                web.post("/clear_cache", self.handle_clear_cache),
            ]
        )
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._cache: dict[str, tuple[ResolvedStream, float]] = {}
        self._cache_ttl_sec: int = RADIKO_CACHE_TTL_SEC
        self._session: aiohttp.ClientSession | None = None

    async def handle_master(self, request: web.Request) -> web.Response:
        """Rewrite the master playlist to point to this proxy."""
        station = request.match_info["station"]
        resolved = await self._ensure_resolved(station)
        if not resolved:
            return web.Response(status=404, text="station not found")
        assert self._session is not None
        try:
            async with self._session.get(
                resolved.m3u8_url, timeout=HTTP_TIMEOUT
            ) as upstream:
                if upstream.status != 200:
                    return web.Response(status=upstream.status, text="upstream error")
                text = await upstream.text()
        except asyncio.TimeoutError:
            return web.Response(status=504, text="upstream timeout")
        except aiohttp.ClientError:
            return web.Response(status=502, text="upstream error")

        base = self._base_url(resolved.m3u8_url)
        out_lines: list[str] = []
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                out_lines.append(line)
                continue
            abs_url = s if "://" in s else urljoin(base, s)
            path = urlparse(abs_url).path
            ext = os.path.splitext(path)[1].lower().lstrip(".")
            if ext not in ("m3u8", "aac", "ts", "mp3", "m4a"):
                ext = "bin"
            out_lines.append(
                f"/seg.{ext}?{urlencode({'u': abs_url, 'station': station})}"
            )
        rewritten = "\n".join(out_lines) + "\n"
        return web.Response(
            status=200,
            text=rewritten,
            headers={
                "Content-Type": "application/vnd.apple.mpegurl",
                "Cache-Control": "no-store, no-cache, must-revalidate",
                "Pragma": "no-cache",
            },
        )

    async def handle_seg(self, request: web.Request) -> web.StreamResponse:
        """Proxy an individual segment request."""
        url = request.query.get("u")
        station = request.query.get("station")
        if not url:
            return web.Response(status=400, text="missing u")
        assert self._session is not None
        for attempt in range(RADIKO_SEGMENT_RETRY_ATTEMPTS):
            try:
                async with self._session.get(url, timeout=HTTP_TIMEOUT) as upstream:
                    if upstream.status == 200:
                        ctype = upstream.headers.get(
                            "Content-Type", "application/octet-stream"
                        )
                        resp = web.StreamResponse(
                            status=200, headers={"Content-Type": ctype}
                        )
                        await resp.prepare(request)
                        async for chunk in upstream.content.iter_chunked(
                            RADIKO_CHUNK_SIZE
                        ):
                            if chunk:
                                await resp.write(chunk)
                        await resp.write_eof()
                        return resp
                    elif upstream.status == 403 and station:
                        self._cache.pop(station, None)
                        import asyncio as _asyncio

                        await _asyncio.sleep(0.15)
                        resolved = await self._ensure_resolved(station)
                        if resolved:
                            old_parsed = urlparse(url)
                            filename = old_parsed.path.split("/")[-1]
                            tail = filename + (
                                f"?{old_parsed.query}" if old_parsed.query else ""
                            )
                            new_base = self._base_url(resolved.m3u8_url)
                            url = f"{new_base}{tail}"
                            continue
                        else:
                            return web.Response(
                                status=503, text="failed to resolve stream"
                            )
                    else:
                        return web.Response(
                            status=upstream.status, text="upstream error"
                        )
            except (asyncio.TimeoutError, aiohttp.ClientError):
                if attempt < RADIKO_SEGMENT_RETRY_ATTEMPTS - 1:
                    if station:
                        self._cache.pop(station, None)
                        await self._ensure_resolved(station)
                    continue
        return web.Response(status=502, text="all attempts failed")

    async def handle_clear_cache(self, request: web.Request) -> web.Response:
        """Clear cached stream resolutions for a station."""
        try:
            data = await request.json()
            station = data.get("station")
            if station:
                self._cache.pop(station, None)
                return web.Response(status=200, text="cache cleared")
        except Exception:
            pass
        return web.Response(status=400, text="invalid request")

    def _base_url(self, url: str) -> str:
        """Return the directory portion of a URL."""
        p = urlparse(url)
        base_path = p.path.rsplit("/", 1)[0]
        return f"{p.scheme}://{p.netloc}{base_path}/"

    async def _ensure_resolved(self, station: str) -> ResolvedStream | None:
        """Resolve and cache stream information for a station."""
        import time

        now = time.monotonic()
        cached = self._cache.get(station)
        ttl = RADIKO_RESOLVE_TTL_SEC
        if cached:
            cached_res, ts = cached
            if now - ts < ttl:
                return cached_res
            else:
                self._cache.pop(station, None)
        await asyncio.sleep(RADIKO_RETRY_DELAY_SEC)
        new_res: ResolvedStream | None = await asyncio.to_thread(
            self._resolver.resolve_live, station
        )
        if new_res:
            self._cache[station] = (new_res, now)
        return new_res

    def start_in_thread(self) -> None:
        """Start the proxy server on a dedicated thread."""

        def runner() -> None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._start())
            self._loop.run_forever()

        t: threading.Thread = threading.Thread(target=runner, daemon=True)
        t.start()

    async def _start(self) -> None:
        """Start the aiohttp server and client session."""
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self.host, self.port)
        await self._site.start()
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
        base = dict(self._resolver.http.headers)
        base.setdefault("User-Agent", base.get("User-Agent", "Mozilla/5.0"))
        base.setdefault("Referer", "https://radiko.jp/")
        base.setdefault("Origin", "https://radiko.jp")
        base.setdefault("Accept", "application/vnd.apple.mpegurl,*/*")
        base.setdefault("Accept-Language", "ja,en-US;q=0.9,en;q=0.8")
        base.setdefault("Cache-Control", "no-cache")
        base.setdefault("Pragma", "no-cache")
        self._session = aiohttp.ClientSession(timeout=timeout, headers=base)

    def stop(self) -> None:
        """Request graceful shutdown of the proxy server."""
        if self._loop:
            self._loop.call_soon_threadsafe(asyncio.create_task, self._shutdown())

    async def _shutdown(self) -> None:
        """Shut down the aiohttp server and release resources."""
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()
        if self._session:
            await self._session.close()
        if self._loop:
            self._loop.stop()
