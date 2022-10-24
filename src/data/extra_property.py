from collections import defaultdict

import dataclasses
import pywikibot

@dataclasses.dataclass
class ExtraQualifier:
    claim: pywikibot.Claim
    skip_if_any_exists: bool = False

@dataclasses.dataclass
class ExtraProperty:
    claim: pywikibot.Claim
    skip_if_any_exists: bool = False
    re_cycle_able: bool = False
    qualifiers: defaultdict[str, list[ExtraQualifier]] = dataclasses.field(default_factory=lambda: defaultdict(list))