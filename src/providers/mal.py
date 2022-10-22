import datetime
from typing import Any
import requests
import pywikibot

from ..abc.provider import Provider
from ..constants import Genres, Demographics, site, stated_at_prop, url_prop, mal_id_prop
from ..data.reference import Reference
from ..data.results import Result
from ..pywikibot_stub_types import WikidataReference

class MALProvider(Provider):
    name: str = "MyAnimeList"

    jikan_base = "https://api.jikan.moe/v4"

    mal_item = pywikibot.ItemPage(site, "Q4044680")

    # Sourced from https://api.jikan.moe/v4/genres/manga

    genre_mapping = {
        1: Genres.action,
        2: Genres.adventure,
        4: Genres.comedy,
        8: Genres.drama,
        10: Genres.fantasy,
        26: Genres.yuri,
        14: Genres.horror,
        7: Genres.mystery,
        22: Genres.romance,
        24: Genres.science_fiction,
        36: Genres.slice_of_life,
        30: Genres.sports,
        37: Genres.supernatural,
        45: Genres.suspense,
        9: Genres.ecchi,
        49: Genres.ecchi, # Wikidata has no item for erotica/smut, use ecchi for now,
        12: Genres.hentai,
        52: Genres.cute_girls_doing_cute_things,
        35: Genres.harem,
        13: Genres.historical,
        62: Genres.isekai,
        65: Genres.gender_bender,
        17: Genres.magical_girl,
        18: Genres.mecha,
        63: Genres.iyashikei,
        40: Genres.psychological,
        74: Genres.harem, # Reverse harem is basically a harem
        77: Genres.survival,
        54: Genres.sports, # Close-combat sports is a type of sports
        78: Genres.sports, # Team sports is a type of sports
        32: Genres.vampire,
        75: Genres.romance
    }

    # Sourced from https://api.jikan.moe/v4/genres/manga?filter=demographics

    demographic_mapping = {
        15: Demographics.children,
        42: Demographics.josei,
        41: Demographics.seinen,
        25: Demographics.shojo,
        27: Demographics.shonen
    }

    def __init__(self):
        self.session = requests.Session()

    def get(self, id: str) -> Result:
        r = self.session.get(f"{self.jikan_base}/manga/{id}/full")
        r.raise_for_status();
        json = r.json()
        data = json["data"]
        ret = Result()
        if data["chapters"]:
            ret.chapters = data["chapters"]
        if data["volumes"]:
            ret.volumes = data["volumes"]
        if data.get("published", {}).get("from", None):
            ret.start_date = datetime.datetime.fromisoformat(data["published"]["from"])
        if data.get("published", {}).get("to", None):
            ret.end_date = datetime.datetime.fromisoformat(data["published"]["to"])
        for genre in data["genres"] + data["explicit_genres"] + data["themes"]:
            if genre["mal_id"] in self.genre_mapping:
                ret.genres.append(self.genre_mapping[genre["mal_id"]])
        for demographic in data["demographics"]:
            if demographic["mal_id"] in self.demographic_mapping:
                ret.demographics.append(self.demographic_mapping[demographic["mal_id"]])
        return ret

    def compute_similar_reference(self, potential_ref: WikidataReference, id: str) -> bool:
        if stated_at_prop in potential_ref:
            for claim in potential_ref[stated_at_prop]:
                if claim.getTarget().id == self.mal_item.id: # type: ignore
                    return True
        if url_prop in potential_ref:
            for claim in potential_ref[url_prop]:
                if f"https://myanimelist.net/manga/{id}" in claim.getTarget().lower(): # type: ignore
                    return True
        if mal_id_prop in potential_ref:
            for claim in potential_ref[mal_id_prop]:
                if claim.getTarget() == id:
                    return True
        return False

    def get_reference(self, id: str) -> Reference:
        return Reference(stated_in=self.mal_item, url=f"https://myanimelist.net/manga/{id}")