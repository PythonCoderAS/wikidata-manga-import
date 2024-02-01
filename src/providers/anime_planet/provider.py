import re

import pywikibot

from ...abc.provider import Provider
from ...constants import (
    Demographics,
    Genres,
    anime_planet_item,
    anime_planet_prop,
    stated_at_prop,
    url_prop,
)
from ...data.reference import Reference
from ...data.results import Result
from ...pywikibot_stub_types import WikidataReference
from .parser import base_url, get_data, ap_new_url_regex

from wikidata_bot_framework import ExtraReference, site, ExtraProperty


class AnimePlanetProvider(Provider):
    name = "Anime-Planet"
    prop = anime_planet_prop

    genre_mapping = {
        "action": Genres.action,
        "adventure": Genres.adventure,
        "autobiographies": Genres.autobiographical,
        "bara": Genres.bara,
        "comedy": Genres.comedy,
        "drama": Genres.drama,
        "dark-fantasy": Genres.dark_fantasy,
        "fantasy": Genres.fantasy,
        "ecchi": Genres.ecchi,
        "gender-bender": Genres.gender_bender,
        "ghosts": Genres.ghost_story,
        "harem": Genres.harem,
        "reverse-harem": Genres.harem,
        "historical": Genres.historical,
        "horror": Genres.horror,
        "isekai": Genres.isekai,
        "reverse-isekai": Genres.isekai,
        "iyashikei": Genres.iyashikei,
        "magical-girl": Genres.magical_girl,
        "mahjong": Genres.mahjong,
        "mecha": Genres.mecha,
        "mystery": Genres.mystery,
        "post-apocalyptic": Genres.post_apocalyptic,
        "psychological": Genres.psychological,
        "romance": Genres.romance,
        "school-life": Genres.school,
        "sci-fi": Genres.science_fiction,
        "slice-of-life": Genres.slice_of_life,
        "sports": Genres.sports,
        "supernatural": Genres.supernatural,
        "survival": Genres.survival,
        "thriller": Genres.thriller,
        "vampires": Genres.vampire,
        "yaoi": Genres.yaoi,
        "yuri": Genres.yuri,
        "zombies": Genres.zombie,
        "shounen": Demographics.shonen,
        "shounen-ai": Genres.yaoi,
        "shoujo": Demographics.shojo,
        "shoujo-ai": Genres.yuri,
        "seinen": Demographics.seinen,
        "josei": Demographics.josei,
    }

    def get(self, id: str, _) -> Result:
        data = get_data(id)
        res = Result()
        if data.bad_data_report:
            res.bad_data_reports.append(data.bad_data_report)
            return res
        if data.previous_urls and data.new_id:
            res.new_id = data.new_id
            # We want to store a list of references just in case a given URL is not a valid ID url.
            previous_references = []
            for url in data.previous_url:
                id_match = ap_new_url_regex.search(url)
                url_ref_claim = pywikibot.Claim(site, url_prop)
                url_ref_claim.setTarget(url)
                current_ref = ExtraReference()
                current_ref.match_property_values[
                    url_prop
                ] = current_ref.new_reference_props[url_prop] = url_ref_claim
                current_ref.new_reference_props[stated_at_prop] = anime_planet_item
                previous_references.append(current_ref)
                if id_match:
                    old_id = id_match.group(1)
                    id_claim = pywikibot.Claim(site, anime_planet_prop)
                    id_claim.setTarget(old_id)
                    id_claim.setRank("deprecated")
                    id_claim_prop = ExtraProperty(id_claim)
                    id_claim_prop.extra_references.extend(previous_references)
                    res.extra_properties.append(id_claim_prop)
            if previous_references:
                new_id_prop = ExtraProperty.from_property_id_and_value(
                    anime_planet_prop, data.new_id
                )
                new_id_prop.extra_references.extend(previous_references)
                res.extra_properties.append(new_id_prop)
        if data.start_year:
            res.start_date = pywikibot.WbTime(year=data.start_year)
        if data.end_year:
            res.end_date = pywikibot.WbTime(year=data.end_year)
        if data.volumes:
            res.volumes = data.volumes
        if data.chapters:
            res.chapters = data.chapters
        for genre in data.tags:
            if genre in self.genre_mapping:
                if isinstance(self.genre_mapping[genre], Genres):
                    res.genres.append(self.genre_mapping[genre])
                else:
                    res.demographics.append(self.genre_mapping[genre])
        return res

    def compute_similar_reference(
        self, potential_ref: WikidataReference, id: str
    ) -> bool:
        if stated_at_prop in potential_ref:
            for claim in potential_ref[stated_at_prop]:
                if claim.getTarget().id == anime_planet_item.id:  # type: ignore
                    return True
        if url_prop in potential_ref:
            for claim in potential_ref[url_prop]:
                base_url_safe = base_url.replace(".", r"\.")
                if re.search(rf"{base_url_safe}/{id}", claim.getTarget().lower()):  # type: ignore
                    return True
        if anime_planet_prop in potential_ref:
            for claim in potential_ref[anime_planet_prop]:
                if claim.getTarget() == id:
                    return True
        return False

    def get_reference(self, id: str) -> Reference:
        return Reference(stated_in=anime_planet_item, url=f"{base_url}/{id}")
