from typing import MutableMapping

import pywikibot

WikidataReference = MutableMapping[str, list[pywikibot.Claim]]
