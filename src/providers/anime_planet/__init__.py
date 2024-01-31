import dataclasses
from typing import Union

from pywikibot import List

from ...data.bad_data import BadDataReport


@dataclasses.dataclass
class ParserResult:
    start_year: Union[int, None] = None
    end_year: Union[int, None] = None
    volumes: Union[int, None] = None
    chapters: Union[int, None] = None
    magazine: List[str] = dataclasses.field(default_factory=list)
    tags: List[str] = dataclasses.field(default_factory=list)
    new_id: str | None = None
    previous_urls: List[str] = dataclasses.field(default_factory=list)
    bad_data_report: BadDataReport | None = None
