from collections import defaultdict

import dataclasses
import datetime

import pywikibot

from .extra_property import ExtraProperty
from ..constants import Genres, Demographics

@dataclasses.dataclass
class Result:
    genres: list[Genres] = dataclasses.field(default_factory=list)
    demographics: list[Demographics] = dataclasses.field(default_factory=list)
    start_date: datetime.datetime| pywikibot.WbTime | None = None
    end_date: datetime.datetime | pywikibot.WbTime | None = None
    en_labels: set[str] = dataclasses.field(default_factory=set)
    volumes: int | None = None
    chapters: int | None = None
    
    other_properties: defaultdict[str, list[ExtraProperty]] = dataclasses.field(default_factory=lambda: defaultdict(list))