import dataclasses
import datetime

from .reference import Reference
from ..constants import Genres, Demographics

@dataclasses.dataclass
class Result:
    reference: Reference

    genres: list[Genres] = dataclasses.field(default_factory=list)
    demographics: list[Demographics] = dataclasses.field(default_factory=list)
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None
    volumes: int | None = None
    chapters: int | None = None