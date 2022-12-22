import dataclasses
import datetime
from collections import defaultdict
from re import Pattern
from typing import Union

import pywikibot

from ..constants import retrieved_prop, site, url_prop
from ..pywikibot_stub_types import WikidataReference


@dataclasses.dataclass
class ExtraQualifier:
    claim: pywikibot.Claim
    skip_if_conflicting_exists: bool = False
    skip_if_conflicting_language_exists: bool = False
    reference_only: bool = False


@dataclasses.dataclass
class ExtraReference:
    match_property_values: dict[str, pywikibot.Claim] = dataclasses.field(
        default_factory=dict
    )
    url_match_pattern: Pattern[Union[str], None] = None
    new_reference_props: dict[str, pywikibot.Claim] = dataclasses.field(
        default_factory=dict
    )

    def is_compatible_reference(self, reference: WikidataReference) -> bool:
        if self.url_match_pattern and url_prop in reference:
            for claim in reference[url_prop]:
                if self.url_match_pattern.match(claim.getTarget()):  # type: ignore
                    return True
        for prop, claim in self.match_property_values.items():
            if prop not in reference:
                continue
            for ref_claim in reference[prop]:
                if ref_claim.getTarget() == claim.getTarget():
                    return True
        return False


@dataclasses.dataclass
class ExtraProperty:
    claim: pywikibot.Claim
    skip_if_conflicting_exists: bool = False
    skip_if_conflicting_language_exists: bool = False
    reference_only: bool = False
    qualifiers: defaultdict[str, list[ExtraQualifier]] = dataclasses.field(
        default_factory=lambda: defaultdict(list)
    )
    extra_references: list[ExtraReference] = dataclasses.field(default_factory=list)
