import re

import pywikibot

from ..abc.provider import Provider
from ..constants import (
    Demographics,
    Genres,
    mu_id_prop,
    mu_item,
    stated_at_prop,
    url_prop,
)
from ..data.reference import Reference
from ..data.results import Result
from ..pywikibot_stub_types import WikidataReference


class MangaUpdatesProvider(Provider):
    name = "MangaUpdates"
    prop = mu_id_prop

    mu_base = "https://api.mangaupdates.com/v1"

    genre_mapping = {
        "Action": Genres.action,
        "Adult": Genres.hentai,
        "Adventure": Genres.adventure,
        "Comedy": Genres.comedy,
        "Drama": Genres.drama,
        "Ecchi": Genres.ecchi,
        "Fantasy": Genres.fantasy,
        "Gender Bender": Genres.gender_bender,
        "Harem": Genres.harem,
        "Hentai": Genres.hentai,
        "Historical": Genres.historical,
        "Horror": Genres.horror,
        "Josei": Demographics.josei,
        "Mature": Genres.hentai,
        "Mecha": Genres.mecha,
        "Mystery": Genres.mystery,
        "Psychological": Genres.psychological,
        "Romance": Genres.romance,
        "School Life": Genres.school,
        "Sci-fi": Genres.science_fiction,
        "Seinen": Demographics.seinen,
        "Shoujo": Demographics.shojo,
        "Shoujo Ai": Genres.yuri,
        "Shounen": Demographics.shonen,
        "Shounen Ai": Genres.yaoi,
        "Slice of Life": Genres.slice_of_life,
        "Smut": Genres.hentai,
        "Sports": Genres.sports,
        "Supernatural": Genres.supernatural,
        "Yaoi": Genres.yaoi,
        "Yuri": Genres.yuri,
    }

    @staticmethod
    def base36_to_int(s: str):
        return int(s, 36)

    def get(self, id: str, _) -> Result:
        id_num = self.base36_to_int(id)
        r, data = self.do_request_with_retries(
            "GET",
            f"{self.mu_base}/series/{id_num}",
            not_found_on_request_404=True,
            retry_on_status_codes=(429,),
        )
        res = Result()
        if r is None or data is None:
            return Result()
        assert isinstance(data, dict)
        for genre_obj in data.get("genres", []):
            genre = genre_obj.get("genre", "")
            genre_enum = self.genre_mapping.get(genre, None)
            if not genre_enum:
                continue
            elif isinstance(genre_enum, Genres):
                res.genres.append(genre_enum)
            elif isinstance(genre_enum, Demographics):
                res.demographics.append(genre_enum)
        year: str = data.get("year", "")
        if year.isnumeric():
            res.start_date = pywikibot.WbTime(year=int(year))
        return res

    def compute_similar_reference(
        self, potential_ref: WikidataReference, id: str
    ) -> bool:
        if stated_at_prop in potential_ref:
            for claim in potential_ref[stated_at_prop]:
                if claim.getTarget().id == mu_item.id:  # type: ignore
                    return True
        if url_prop in potential_ref:
            for claim in potential_ref[url_prop]:
                if re.search(
                    rf"https://www\.mangaupdates\.com/series/{id}",
                    claim.getTarget().lower(),
                ):  # type: ignore
                    return True
        if mu_id_prop in potential_ref:
            for claim in potential_ref[mu_id_prop]:
                if claim.getTarget() == id:
                    return True
        return False

    def get_reference(self, id: str) -> Reference:
        return Reference(
            stated_in=mu_item, url=f"https://www.mangaupdates.com/series/{id}"
        )
