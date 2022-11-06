import pywikibot

from ..data.extra_property import ExtraProperty, ExtraQualifier, ExtraReference
from ..data.smart_precision_time import SmartPrecisionTime

from ..abc.provider import Provider
from ..constants import Genres, Demographics, site, stated_at_prop, url_prop, mal_id_prop, japan_item, japanese_lang_item, korea_item, korean_lang_item, china_item, chinese_lang_item, country_prop, language_prop, hashtag_prop, anilist_id_prop, official_site_prop, romaji_title_prop, title_prop
from ..data.reference import Reference
from ..data.results import Result
from ..pywikibot_stub_types import WikidataReference