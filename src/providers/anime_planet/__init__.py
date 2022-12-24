import dataclasses
from typing import Union

from pywikibot import List


@dataclasses.dataclass
class ParserResult:
    start_year: Union[int, None] = None
    end_year: Union[int, None] = None
    volumes: Union[int, None] = None
    chapters: Union[int, None] = None
    magazine: List[str] = dataclasses.field(default_factory=list)
    tags: List[str] = dataclasses.field(default_factory=list)
