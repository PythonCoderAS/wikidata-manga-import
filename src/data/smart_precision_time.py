from typing import Optional

import pywikibot


class SmartPrecisionTime(pywikibot.WbTime):
    def __init__(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
        **kwargs,
    ):
        if month is None and day is None:
            kwargs.setdefault("precision", pywikibot.WbTime.PRECISION["year"])
        elif day is None:
            kwargs.setdefault("precision", pywikibot.WbTime.PRECISION["month"])
        super().__init__(year, month, day, **kwargs)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, pywikibot.WbTime):
            return self.toWikibase() == other.toWikibase()
        return NotImplemented
