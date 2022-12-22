import dataclasses
from typing import Union

import pywikibot


@dataclasses.dataclass
class Link:
    url: str
    """The item for the language of the link."""
    language: Union[pywikibot.ItemPage, None] = None
