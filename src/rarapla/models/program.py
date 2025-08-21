"""Data model for program details."""

from dataclasses import dataclass


@dataclass
class Program:
    """Details about a radio program.

    Attributes:
        title: Program title.
        pfm: Performer or host of the program.
        desc: Short description of the program.
        image: URL to an image representing the program.
    """

    title: str
    pfm: str | None = None
    desc: str | None = None
    image: str | None = None
