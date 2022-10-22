import dataclasses
import pywikibot

@dataclasses.dataclass
class ExtraProperty:
    claim: pywikibot.Claim
    skip_if_any_exists: bool = False