import dataclasses
import datetime

from ..constants import Genres, Demographics

@dataclasses.dataclass
class Result:
    genres: list[Genres] = dataclasses.field(default_factory=list)
    demographics: list[Demographics] = dataclasses.field(default_factory=list)
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None
    volumes: int | None = None
    chapters: int | None = None