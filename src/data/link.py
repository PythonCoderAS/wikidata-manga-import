import dataclasses

import pywikibot

@dataclasses.dataclass
class Link:
    url: str
    """The item for the language of the link."""
    language: pywikibot.ItemPage | None = None