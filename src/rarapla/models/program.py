from dataclasses import dataclass

@dataclass
class Program:
    title: str
    pfm: str | None = None
    desc: str | None = None
    image: str | None = None
