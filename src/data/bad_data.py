import dataclasses
import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING, Self

import pywikibot

if TYPE_CHECKING:
    from ..abc.provider import Provider


@dataclasses.dataclass
class BadDataReport:
    provider: "Provider"
    provider_id: str
    message: str
    data: Optional[Dict[str, Any]] = None
    report_time: pywikibot.Timestamp = pywikibot.Timestamp.now(datetime.timezone.utc)

    @classmethod
    def from_duplicate_extra_item_linkage(
        cls,
        provider: "Provider",
        provider_id: str,
        prop_id: str,
        search_value: str,
        item_ids: list[str],
    ) -> Self:
        msg = "Duplicate items found for {{P|%(prop_id)s}} -> %(search_value)s:\n\n%(item_ids_str)s"
        item_ids_str = "\n".join(
            "* {{Q|%(item_id)s}}" % {"item_id": item_id} for item_id in item_ids
        )

        return cls(
            provider=provider,
            provider_id=provider_id,
            message=msg
            % {
                "prop_id": prop_id,
                "search_value": search_value,
                "item_ids_str": item_ids_str,
            },
        )
