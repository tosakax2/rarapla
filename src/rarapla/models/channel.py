"""Data models for representing radio channels."""

from dataclasses import dataclass


@dataclass
class Channel:
    """A radio channel currently broadcasting a program.

    Attributes:
        id: Station identifier.
        name: Display name for the station.
        logo_url: URL to the station logo image if available.
        program_title: Title of the program that is on air.
        program_image: URL to an image representing the program.
        stream_url: Direct stream URL when known.
    """

    id: str
    name: str
    logo_url: str | None
    program_title: str
    program_image: str | None
    stream_url: str | None = None
