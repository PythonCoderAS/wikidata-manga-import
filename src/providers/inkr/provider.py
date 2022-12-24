import re

import pywikibot

from ...abc.provider import Provider
from ...constants import Genres, inkr_item, inkr_prop, stated_at_prop, url_prop
from ...data.reference import Reference
from ...data.results import Result
from ...pywikibot_stub_types import WikidataReference
from .parser import base_url, get_data


class INKRProvider(Provider):
    name = "INKR"

    genre_mapping = {
        1: Genres.supernatural,
        2: Genres.action,
        3: Genres.comedy,
        5: Genres.romance,
        6: Genres.ecchi,
        7: Genres.school,
        8: Genres.adventure,
        9: Genres.fantasy,
        11: Genres.psychological,
        12: Genres.drama,
        13: Genres.slice_of_life,
        14: Genres.yaoi,
        15: Genres.mecha,
        16: Genres.horror,
        17: Genres.thriller,
        18: Genres.historical,
        19: Genres.yaoi,
        20: Genres.sports,
        22: Genres.vampire,
        24: Genres.mystery,
        26: Genres.yaoi,
        27: Genres.science_fiction,
        28: Genres.yaoi,
        30: Genres.yuri,
        33: Genres.yaoi,
        38: Genres.isekai,
        43: Genres.harem,
        58: Genres.hentai,
        59: Genres.historical,
        62: Genres.gender_bender,
        88: Genres.hentai,
        92: Genres.suspense,
        94: Genres.cute_girls_doing_cute_things,
        109: Genres.gender_bender,
        110: Genres.magical_girl,
        120: Genres.harem,
        127: Genres.survival,
        128: Genres.sports,
        153: Genres.zombie,
    }

    def get(self, id: str, _) -> Result:
        data = get_data(id)
        res = Result()
        for genre_id in data.genres:
            if genre := self.genre_mapping.get(int(genre_id), None):
                res.genres.append(genre)
        return res

    def compute_similar_reference(
        self, potential_ref: WikidataReference, id: str
    ) -> bool:
        if stated_at_prop in potential_ref:
            for claim in potential_ref[stated_at_prop]:
                if claim.getTarget().id == inkr_item.id:  # type: ignore
                    return True
        if url_prop in potential_ref:
            for claim in potential_ref[url_prop]:
                if re.search(rf"{base_url}/{id}", claim.getTarget().lower()):  # type: ignore
                    return True
        if inkr_prop in potential_ref:
            for claim in potential_ref[inkr_prop]:
                if claim.getTarget() == id:
                    return True
        return False

    def get_reference(self, id: str) -> Reference:
        return Reference(stated_in=inkr_item, url=f"{base_url}/{id}")
