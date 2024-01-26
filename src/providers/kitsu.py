import re

import pywikibot
from wikidata_bot_framework import EntityPage, Output

from ..abc.provider import Provider
from ..constants import (
    Demographics,
    Genres,
    kitsu_item,
    kitsu_prop,
    stated_at_prop,
    url_prop,
)
from ..data.reference import Reference
from ..data.results import Result
from ..exceptions import NotFoundException
from ..pywikibot_stub_types import WikidataReference


class KitsuProvider(Provider):
    name = "Kitsu"
    prop = kitsu_prop

    kitsu_base = "https://kitsu.io/api/edge"

    genre_mapping = {
        3: Genres.school,
        7: Genres.vampire,
        22: Genres.school,
        28: Genres.zombie,
        37: Genres.magical_girl,
        38: Genres.ghost_story,
        40: Genres.lolicon,
        52: Genres.fantasy,
        59: Genres.mecha,
        62: Genres.historical,
        68: Genres.fantasy,
        69: Genres.fantasy,
        70: Genres.dark_fantasy,
        71: Genres.comedy,
        73: Genres.comedy,
        80: Genres.school,
        111: Genres.sports,
        112: Genres.sports,
        113: Genres.sports,
        122: Genres.yuri,
        123: Genres.yaoi,
        130: Genres.harem,
        133: Genres.sports,
        150: Genres.action,
        155: Genres.science_fiction,
        156: Genres.fantasy,
        157: Genres.adventure,
        158: Genres.horror,
        159: Genres.thriller,
        160: Genres.comedy,
        162: Genres.ecchi,
        164: Genres.romance,
        165: Genres.harem,
        169: Genres.slice_of_life,
        172: Genres.school,
        180: Genres.spokon,
        184: Genres.drama,
        197: Genres.post_apocalyptic,
        222: Genres.sports,
        232: Genres.psychological,
        233: Genres.supernatural,
        234: Genres.mystery,
        235: Genres.gender_bender,
        236: Genres.yaoi,
        239: Demographics.children,
        242: Demographics.shojo,
        243: Demographics.shonen,
        244: Demographics.seinen,
        245: Demographics.josei,
        246: Genres.isekai,
    }

    def get(self, id: str, _) -> Result:
        non_numeric = False
        if not id.isnumeric():
            non_numeric = True
        if non_numeric:
            url = f"{self.kitsu_base}/manga"
            params = {
                "fields[categories]": "id",
                "filter[slug]": id,
                "page[limit]": 1,
                "page[offset]": 0,
                "include": "categories",
            }
            r, data = self.do_request_with_retries("GET", url, params=params)
            if r is None or data is None:
                return Result()
            assert isinstance(data, dict)
            if data["meta"]["count"] == 0:
                raise NotFoundException(r)
            elif data["meta"]["count"] != 1:
                raise ValueError(
                    f"Multiple results found, this should not be happening. Input slug: {id}"
                )
            actual_data = data["data"][0]
            id = actual_data["id"]
        else:
            url = f"{self.kitsu_base}/manga/{id}"
            params = {"fields[categories]": "id", "include": "categories"}
            r, data = self.do_request_with_retries(
                "GET", url, params=params, not_found_on_request_404=True
            )
            if r is None or data is None:
                return Result()
            assert isinstance(data, dict)
            actual_data = data["data"]
        if "included" in data:
            categories = [int(item["id"]) for item in data["included"]]
        else:
            categories = []
        result = Result()
        attributes = actual_data["attributes"]
        genres = [
            self.genre_mapping[genre]
            for genre in categories
            if genre in self.genre_mapping
        ]
        result.genres = genres
        if attributes["startDate"]:
            result.start_date = pywikibot.WbTime.fromTimestamp(
                pywikibot.Timestamp.strptime(attributes["startDate"], "%Y-%m-%d")
            )  # type: ignore
        if attributes["endDate"]:
            result.end_date = pywikibot.WbTime.fromTimestamp(
                pywikibot.Timestamp.strptime(attributes["endDate"], "%Y-%m-%d")
            )  # type: ignore
        if attributes["volumeCount"]:
            result.volumes = attributes["volumeCount"]
        if attributes["chapterCount"]:
            result.chapters = attributes["chapterCount"]
        return result

    def post_process_hook(self, output: Output, item: EntityPage) -> bool:
        edited = False
        for claim in item.claims.get(self.prop, []).copy():
            if not claim.getTarget().isnumeric():
                item.claims[self.prop].remove(claim)
                edited = True
        return edited

    def compute_similar_reference(
        self, potential_ref: WikidataReference, id: str
    ) -> bool:
        if stated_at_prop in potential_ref:
            for claim in potential_ref[stated_at_prop]:
                if claim.getTarget().id == kitsu_item.id:  # type: ignore
                    return True
        if url_prop in potential_ref:
            for claim in potential_ref[url_prop]:
                if re.search(
                    rf"https://kitsu\.io/manga/{id}", claim.getTarget().lower()
                ):  # type: ignore
                    return True
        if kitsu_prop in potential_ref:
            for claim in potential_ref[kitsu_prop]:
                if claim.getTarget() == id:
                    return True
        return False

    def get_reference(self, id: str) -> Reference:
        return Reference(stated_in=kitsu_item, url=f"https://kitsu.io/manga/{id}")
