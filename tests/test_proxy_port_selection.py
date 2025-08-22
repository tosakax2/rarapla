import socket
from rarapla.config import PROXY_PORT
from rarapla.proxy.radiko_proxy import RadikoProxyServer


def test_default_port_fallback() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", PROXY_PORT))
        s.listen()
        proxy = RadikoProxyServer()
        assert proxy.port == PROXY_PORT + 1
