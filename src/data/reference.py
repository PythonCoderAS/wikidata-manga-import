import dataclasses

import pywikibot


@dataclasses.dataclass
class Reference:
    stated_in: pywikibot.ItemPage
    url: str
