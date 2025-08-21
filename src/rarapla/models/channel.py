from dataclasses import dataclass

@dataclass
class Channel:
    id: str
    name: str
    logo_url: str | None
    program_title: str
    program_image: str | None
    stream_url: str | None = None
