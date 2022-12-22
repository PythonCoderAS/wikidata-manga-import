import dataclasses
import datetime

import pywikibot


@dataclasses.dataclass
class Reference:
    stated_in: pywikibot.ItemPage
    url: str
    retrieved: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
