import dataclasses
from typing import Union

from wikidata_bot_framework import EntityPage


@dataclasses.dataclass
class Link:
    url: str
    """The item for the language of the link."""
    language: Union[EntityPage, None] = None
