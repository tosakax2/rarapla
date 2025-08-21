"""Application-wide configuration constants."""

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0'
)

# Proxy settings
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 3032

# Network
HTTP_TIMEOUT = 10

# Window geometry
WINDOW_MIN_HEIGHT = 400
WINDOW_DEFAULT_HEIGHT = 720

# Audio
AUDIO_MIN_VOLUME = 0
AUDIO_MAX_VOLUME = 100
AUDIO_DEFAULT_VOLUME = 33

# Radiko proxy parameters
RADIKO_CACHE_TTL_SEC = 5 * 60
RADIKO_SEGMENT_RETRY_ATTEMPTS = 3
RADIKO_CHUNK_SIZE = 64 * 1024
RADIKO_RESOLVE_TTL_SEC = 3 * 60
RADIKO_RETRY_DELAY_SEC = 0.1
