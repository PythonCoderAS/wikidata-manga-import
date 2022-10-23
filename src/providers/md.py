import re

import requests
import pywikibot

from ..abc.provider import Provider
from ..constants import Genres, Demographics, site, stated_at_prop, url_prop, mal_id_prop, japan_item, japanese_lang_item, korea_item, korean_lang_item, china_item, chinese_lang_item, country_prop, language_prop, anilist_id_prop, md_id_prop
from ..data.reference import Reference
from ..data.results import Result
from ..data.extra_property import ExtraProperty
from ..pywikibot_stub_types import WikidataReference

class MangadexProvider(Provider):
    name = "MangaDex"

    md_base = "https://api.mangadex.org"

    md_item = pywikibot.ItemPage(site, "Q110093307")

    # Sourced from https://api.mangadex.org/manga/tag

    genre_map = {
        "07251805-a27e-4d59-b488-f0bfbec15168": Genres.thriller,
        "256c8bd9-4904-4360-bf4f-508a76d67183": Genres.science_fiction,
        "2bd2e8d0-f146-434a-9b51-fc9ff2c5fe6a": Genres.gender_bender,
        "33771934-028e-4cb3-8744-691e866a923e": Genres.historical,
        "391b0423-d847-456f-aff0-8b0cfc03066b": Genres.action,
        "3b60b75c-a2d7-4860-ab56-05f391bb889c": Genres.psychological,
        "3bb26d85-09d5-4d2e-880c-c34b974339e9": Genres.ghost_story,
        "423e2eae-a7a2-4a8b-ac03-a8351462d71d": Genres.romance,
        "4d32cc48-9f00-4cca-9b5a-a839f0764984": Genres.comedy,
        "50880a9d-5440-4732-9afb-8f457127e836": Genres.mecha,
        "5920b825-4181-4a17-beeb-9918b0ff7a30": Genres.yaoi,
        "5fff9cde-849c-4d78-aab0-0d52b2ee1d25": Genres.survival,
        "631ef465-9aba-4afb-b0fc-ea10efe274a8": Genres.zombie,
        "65761a2a-415e-47f3-bef2-a9dababba7a6": Genres.harem, # Reverse harem = harem
        "69964a64-2f90-4d33-beeb-f3ed2875eb4c": Genres.sports,
        "81c836c9-914a-4eca-981a-560dad663e73": Genres.magical_girl,
        "87cc87cd-a395-47af-b27a-93258283bbc6": Genres.adventure,
        "a3c67850-4684-404e-9b7f-c69850ee5da6": Genres.yuri,
        "aafb99c1-7f60-43fa-b75f-fc9502ce29c7": Genres.harem,
        "ace04997-f6bd-436e-b261-779182193d3d": Genres.isekai,
        "b9af3a63-f058-46de-a9a0-e0c13906197a": Genres.drama,
        "caaa44eb-cd40-4177-b930-79d3ef2afe87": Genres.school,
        "cdad7e68-1419-41dd-bdce-27753074a640": Genres.horror,
        "cdc58593-87dd-415e-bbc0-2ec27bf404cc": Genres.fantasy,
        "d7d1730f-6eb0-4ba6-9437-602cac38664c": Genres.vampire,
        "ddefd648-5140-4e5f-ba18-4eca4071d19b": Genres.shotacon,
        "e5301a23-ebd9-49dd-a0cb-2add944c7fe9": Genres.slice_of_life,
        "eabc5b4c-6aff-42f3-b657-3e90cbd00b75": Genres.supernatural,
        "ee968100-4191-4968-93d3-f82d72be7e46": Genres.mystery,
    }

    demographic_map = {
        "shounen": Demographics.shonen,
        "shoujo": Demographics.shojo,
        "josei": Demographics.josei,
        "seinen": Demographics.seinen
    }

    country_code_mapping: dict[str, tuple[pywikibot.ItemPage, pywikibot.ItemPage]] = {
        "ja": (japan_item, japanese_lang_item),
        "ko": (korea_item, korean_lang_item),
        "zh": (china_item, chinese_lang_item),
        "zh-hk": (china_item, chinese_lang_item)
    }

    def __init__(self):
        self.session = requests.Session()
    
    def get(self, id: str) -> Result:
        r = self.session.get(f"{self.md_base}/manga/{id}")
        r.raise_for_status()
        json = r.json()
        data = json["data"]["attributes"]
        result = Result()
        if data["tags"]:
            for tag in data["tags"]:
                if tag["id"] in self.genre_map:
                    result.genres.append(self.genre_map[tag["id"]])
        if data["publicationDemographic"]:
            if data["publicationDemographic"] in self.demographic_map:
                result.demographics.append(self.demographic_map[data["publicationDemographic"]])
        if data["originalLanguage"]:
            if data["originalLanguage"] in self.country_code_mapping:
                country, language = self.country_code_mapping[data["originalLanguage"]]
                country_claim = pywikibot.Claim(site, country_prop)
                country_claim.setTarget(country)
                result.other_properties[country_prop] = ExtraProperty(claim=country_claim, skip_if_any_exists=True)
                language_claim = pywikibot.Claim(site, language_prop)
                language_claim.setTarget(language)
                result.other_properties[language_prop] = ExtraProperty(claim=language_claim)
        if data["lastVolume"]:
            try:
                result.volumes = int(data["lastVolume"])
            except ValueError:
                pass
        if data["lastChapter"]:
            try:
                result.chapters = int(data["lastChapter"])
            except ValueError:
                pass
        # Not a reliable indicator of ecchi-ness.
        # if data["contentRating"] == "suggestive" or data["contentRating"] == "erotica":
        #     result.genres.append(Genres.ecchi)
        if data["contentRating"] == "pornographic":
            result.genres.append(Genres.hentai)
        if data["links"]:
            mal_id = data["links"].get("mal", None)
            if mal_id:
                claim = pywikibot.Claim(site, mal_id_prop)
                claim.setTarget(str(mal_id))
                result.other_properties[mal_id_prop] = ExtraProperty(claim=claim, re_cycle_able=True)
            anilist_id = data["links"].get("al", None)
            if anilist_id:
                claim = pywikibot.Claim(site, anilist_id_prop)
                claim.setTarget(str(anilist_id))
                result.other_properties[anilist_id_prop] = ExtraProperty(claim=claim, re_cycle_able=True)
        return result

    def compute_similar_reference(self, potential_ref: WikidataReference, id: str) -> bool:
        if stated_at_prop in potential_ref:
            for claim in potential_ref[stated_at_prop]:
                if claim.getTarget().id == self.md_item.id: # type: ignore
                    return True
        if url_prop in potential_ref:
            for claim in potential_ref[url_prop]:
                if re.search(rf"https://mangadex.org/(manga|title)/{id}", claim.getTarget().lower()): # type: ignore
                    return True
        if md_id_prop in potential_ref:
            for claim in potential_ref[md_id_prop]:
                if claim.getTarget() == id:
                    return True
        return False

    def get_reference(self, id: str) -> Reference:
        return Reference(stated_in=self.md_item, url=f"https://mangadex.org/title/{id}")