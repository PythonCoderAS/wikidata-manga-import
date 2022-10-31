from collections import defaultdict

import dataclasses
import pywikibot

@dataclasses.dataclass
class ExtraQualifier:
    claim: pywikibot.Claim
    skip_if_conflicting_exists: bool = False
    skip_if_conflicting_language_exists: bool = False
    reference_only: bool = False

@dataclasses.dataclass
class ExtraProperty:
    claim: pywikibot.Claim
    skip_if_conflicting_exists: bool = False
    skip_if_conflicting_language_exists: bool = False
    reference_only: bool = False
    re_cycle_able: bool = False
    qualifiers: defaultdict[str, list[ExtraQualifier]] = dataclasses.field(default_factory=lambda: defaultdict(list))