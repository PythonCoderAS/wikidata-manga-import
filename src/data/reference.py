import dataclasses
import pywikibot
import datetime


@dataclasses.dataclass
class Reference:
    stated_in: pywikibot.ItemPage
    url: str
    retrieved: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
