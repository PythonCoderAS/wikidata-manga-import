import enum
import re

import pywikibot
from requests_cache import CachedSession

site: pywikibot.DataSite = pywikibot.Site("wikidata", "wikidata")  # type: ignore

# Constants for ids of properties that may be created
genre_prop = "P136"
demographic_prop = "P2360"
start_prop = "P580"
country_prop = "P495"
language_prop = "P407"
hashtag_prop = "P2572"
num_parts_prop = "P2635"
title_prop = "P1476"
romaji_title_prop = "P2125"
described_at_url_prop = "P973"

# Constants for ids of qualifiers
retrieved_prop = "P813"
stated_at_prop = "P248"
url_prop = "P854"
archive_url_prop = "P1065"
archive_date_prop = "P2960"
deprecated_reason_prop = "P2241"

# Constants for properties of sources that we pull from
mal_id_prop = "P4087"
anilist_id_prop = "P8731"
md_id_prop = "P10589"
mu_id_prop = "P11149"

# Constants for external IDs of sources that we do not pull from
niconico_prop = "P11176"
bookwalker_prop = "P11259"
inkr_prop = "P11315"
anime_news_network_prop = "P1984"
media_arts_prop = "P7886"
bgm_prop = "P5732"
animeclick_prop = "P5849"

# Information for automatic mode
automated_create_properties = [
    mal_id_prop,
    anilist_id_prop,
    md_id_prop,
    mu_id_prop,
    niconico_prop,
    bookwalker_prop,
    inkr_prop,
    anime_news_network_prop,
    media_arts_prop,
    bgm_prop,
    animeclick_prop,
    num_parts_prop,
    demographic_prop,
]
automated_scan_properties = [mal_id_prop, anilist_id_prop, md_id_prop, mu_id_prop]
url_properties = [described_at_url_prop]
url_blacklist: list[str | re.Pattern] = [
    "twitter.com",
    "youtube.com",
    "instagram.com",
    "pixiv.com",
    "pixiv.net",
]

# Items for countries
japan_item = pywikibot.ItemPage(site, "Q17")
korea_item = pywikibot.ItemPage(site, "Q884")
china_item = pywikibot.ItemPage(site, "Q148")

# Items for languages
japanese_lang_item = pywikibot.ItemPage(site, "Q5287")
korean_lang_item = pywikibot.ItemPage(site, "Q9176")
chinese_lang_item = pywikibot.ItemPage(site, "Q7850")
english_lang_item = pywikibot.ItemPage(site, "Q1860")

# Misc items
volume_item = pywikibot.ItemPage(site, "Q1238720")
link_rot_item = pywikibot.ItemPage(site, "Q1193907")

# Items for sources we pull from
mal_item = pywikibot.ItemPage(site, "Q4044680")
anilist_item = pywikibot.ItemPage(site, "Q86470198")
md_item = pywikibot.ItemPage(site, "Q110093307")
mu_item = pywikibot.ItemPage(site, "Q114730827")

# Regexes for matching external IDs
niconico_regex = re.compile(r"seiga\.nicovideo\.jp/comic/(\d+)")
bookwalker_regex = re.compile(r"(?:(?!:global).)*bookwalker\.jp/(?:series|book)/(\d+)")
inkr_regex = re.compile(r"comics\.inkr\.com/title/(\d+)")
anime_news_network_regex = re.compile(
    r"animenewsnetwork\.com/encyclopedia/manga\.php\?id=(\d+)"
)
media_arts_regex = re.compile(r"mediaarts-db\.bunka.go\.jp/id/C(\d+)")
bgm_regex = re.compile(r"bgm\.tv/subject/(\d+)")
animeclick_regex = re.compile(r"animeclick\.it/manga/(\d+)")


class Genres(enum.Enum):
    action = pywikibot.ItemPage(site, "Q15637293")
    adventure = pywikibot.ItemPage(site, "Q15712918")
    bara = pywikibot.ItemPage(site, "Q18655723")
    comedy = pywikibot.ItemPage(site, "Q15286013")
    comedy_drama = pywikibot.ItemPage(site, "Q15712927")
    cute_girls_doing_cute_things = pywikibot.ItemPage(site, "Q101441130")
    dark_fantasy = pywikibot.ItemPage(site, "Q111254005")
    drama = pywikibot.ItemPage(site, "Q15637299")
    ecchi = pywikibot.ItemPage(site, "Q219559")
    fantasy = pywikibot.ItemPage(site, "Q15637301")
    gender_bender = pywikibot.ItemPage(site, "Q112224709")
    ghost_story = pywikibot.ItemPage(site, "Q111254004")
    harem = pywikibot.ItemPage(site, "Q690342")
    hentai = pywikibot.ItemPage(site, "Q172067")
    historical = pywikibot.ItemPage(site, "Q101240934")
    horror = pywikibot.ItemPage(site, "Q12767035")
    isekai = pywikibot.ItemPage(site, "Q53911753")
    iyashikei = pywikibot.ItemPage(site, "Q97358333")
    magical_girl = pywikibot.ItemPage(site, "Q752321")
    mahjong = pywikibot.ItemPage(site, "Q382236")
    mecha = pywikibot.ItemPage(site, "Q4292083")
    mystery = pywikibot.ItemPage(site, "Q15637305")
    post_apocalyptic = pywikibot.ItemPage(site, "Q103016666")
    psychological = pywikibot.ItemPage(site, "Q101240583")
    romance = pywikibot.ItemPage(site, "Q15637310")
    romantic_comedy = pywikibot.ItemPage(site, "Q15712145")
    school = pywikibot.ItemPage(site, "Q5366097")
    science_fiction = pywikibot.ItemPage(site, "Q5366020")
    shotacon = pywikibot.ItemPage(site, "Q597887")
    slice_of_life = pywikibot.ItemPage(site, "Q15428604")
    spokon = pywikibot.ItemPage(site, "Q2281511")
    sports = pywikibot.ItemPage(site, "Q11313192")
    supernatural = pywikibot.ItemPage(site, "Q61942616")
    survival = pywikibot.ItemPage(site, "Q100965156")
    suspense = pywikibot.ItemPage(site, "Q101240878")
    thriller = pywikibot.ItemPage(site, "Q101240755")
    vampire = pywikibot.ItemPage(site, "Q111019582")
    werewolf = pywikibot.ItemPage(site, "Q113259305")
    yaoi = pywikibot.ItemPage(site, "Q242488")
    yuri = pywikibot.ItemPage(site, "Q320568")
    zombie = pywikibot.ItemPage(site, "Q113259324")


class Demographics(enum.Enum):
    seinen = pywikibot.ItemPage(site, "Q237338")
    shonen = pywikibot.ItemPage(site, "Q231302")
    children = pywikibot.ItemPage(site, "Q478804")
    shojo = pywikibot.ItemPage(site, "Q242492")
    josei = pywikibot.ItemPage(site, "Q503106")


language_item_to_code_map = {
    japanese_lang_item: "ja",
    korean_lang_item: "ko",
    chinese_lang_item: "zh",
}

session = CachedSession(backend="memory")
session.headers[
    "user-agent"
] = "AniMangaDBImportBot/Wikidata (https://wikidata.org/wiki/User:AniMangaDBImportBot) (abuse: https://wikidata.org/wiki/User_talk:RPI2026F1)"
