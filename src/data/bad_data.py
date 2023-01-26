import dataclasses
import datetime
from typing import Any, Dict, Optional

import pywikibot

from ..abc.provider import Provider


@dataclasses.dataclass
class BadDataReport:
    provider: Provider
    provider_id: str
    message: str
    data: Optional[Dict[str, Any]] = None
    report_time: pywikibot.Timestamp = pywikibot.Timestamp.now(datetime.timezone.utc)
