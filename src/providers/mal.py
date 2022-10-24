import datetime
import re
from unittest import skip
import requests
import pywikibot

from ..abc.provider import Provider
from ..constants import Genres, Demographics, site, stated_at_prop, url_prop, mal_id_prop, official_site_prop, language_prop
from ..data.extra_property import ExtraProperty, ExtraQualifier
from ..data.reference import Reference
from ..data.results import Result
from ..pywikibot_stub_types import WikidataReference

class MALProvider(Provider):
    name: str = "MyAnimeList"

    jikan_base = "https://api.jikan.moe/v4"

    year_regex = re.compile(r"\d{4}")

    month_year_regex = re.compile(r"[A-Z][a-z]{2} \d{4}")

    month_day_year_regex = re.compile(r"[A-Z][a-z]{2} \d{1,2}, \d{4}")

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

    @classmethod
    def get_precision(cls, date_string) -> int | None:
        if cls.month_day_year_regex.match(date_string):
            return pywikibot.WbTime.PRECISION["day"]
        elif cls.month_year_regex.match(date_string):
            return pywikibot.WbTime.PRECISION["month"]
        elif cls.year_regex.match(date_string):
            return pywikibot.WbTime.PRECISION["year"]

    def get(self, id: str, item: pywikibot.ItemPage) -> Result:
        r = self.session.get(f"{self.jikan_base}/manga/{id}/full")
        r.raise_for_status();
        json = r.json()
        data = json["data"]
        result = Result()
        if data["chapters"]:
            result.chapters = data["chapters"]
        if data["volumes"]:
            result.volumes = data["volumes"]
        if data.get("published", {}):
            start_date_str, end_date_str = data["published"]["string"].split(" to ")
            if data.get("published", {}).get("from", None):
                dt = datetime.datetime.fromisoformat(data["published"]["from"])
                result.start_date = pywikibot.WbTime(year=dt.year, month=dt.month, day=dt.day, precision=self.get_precision(start_date_str))
            if data.get("published", {}).get("to", None):
                dt = datetime.datetime.fromisoformat(data["published"]["to"])
                result.end_date = pywikibot.WbTime(year=dt.year, month=dt.month, day=dt.day, precision=self.get_precision(end_date_str))
        for genre in data["genres"] + data["explicit_genres"] + data["themes"]:
            if genre["mal_id"] in self.genre_mapping:
                result.genres.append(self.genre_mapping[genre["mal_id"]])
        for demographic in data["demographics"]:
            if demographic["mal_id"] in self.demographic_mapping:
                result.demographics.append(self.demographic_mapping[demographic["mal_id"]])
        for external_item in data["external"]:
            if external_item["name"] == "Official Site":
                claim = pywikibot.Claim(site, official_site_prop)
                claim.setTarget(external_item["url"])
                result.other_properties[official_site_prop].append(ExtraProperty(claim))
                if item.claims[language_prop]:
                    language_item = item.claims[language_prop][0].getTarget()
                    language_claim = pywikibot.Claim(site, language_prop)
                    language_claim.setTarget(language_item)
                    result.other_properties[official_site_prop][-1].qualifiers[language_prop].append(ExtraQualifier(language_claim, skip_if_any_exists=True))
        return result

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