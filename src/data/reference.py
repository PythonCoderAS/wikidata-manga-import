import dataclasses
from datetime import datetime
import string
import pywikibot
import datetime

@dataclasses.dataclass
class Reference:
    stated_in: pywikibot.ItemPage
    url: string
    retrieved: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
