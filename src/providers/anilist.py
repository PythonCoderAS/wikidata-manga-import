import pywikibot

from ..abc.provider import Provider
from ..constants import (
    Demographics,
    Genres,
    anilist_id_prop,
    anilist_item,
    china_item,
    chinese_lang_item,
    country_prop,
    hashtag_prop,
    japan_item,
    japanese_lang_item,
    korea_item,
    korean_lang_item,
    language_prop,
    mal_id_prop,
    site,
    stated_at_prop,
    title_prop,
    url_prop,
)
from ..data.extra_property import ExtraProperty
from ..data.link import Link
from ..data.reference import Reference
from ..data.results import Result
from ..data.smart_precision_time import SmartPrecisionTime
from ..pywikibot_stub_types import WikidataReference


class AnilistProvider(Provider):
    name = "AniList"

    anilist_base = "https://graphql.anilist.co"

    query = """
    query($id: Int){
        Media(id:$id, type:MANGA){
            idMal
            genres,
            tags {
                name
            }
            startDate {
                year,
                month,
                day
            },
            endDate {
                year
                month
                day
            },
            chapters,
            volumes,
            countryOfOrigin,
            hashtag,
            isAdult,
            externalLinks {
                language
                url
                type
            }
            title {
                romaji
                english
                native
            }
        }
}
    """

    # Sourced from https://anilist.co/forum/thread/4824

    genre_mapping = {
        "Action": Genres.action,
        "Adventure": Genres.adventure,
        "Comedy": Genres.comedy,
        "Drama": Genres.drama,
        "Ecchi": Genres.ecchi,
        "Fantasy": Genres.fantasy,
        "Horror": Genres.horror,
        "Mahou Shoujo": Genres.magical_girl,
        "Mecha": Genres.mecha,
        "Mystery": Genres.mystery,
        "Psychological": Genres.psychological,
        "Romance": Genres.romance,
        "Sci-Fi": Genres.science_fiction,
        "Slice of Life": Genres.slice_of_life,
        "Sports": Genres.sports,
        "Supernatural": Genres.supernatural,
        "Thriller": Genres.thriller,
        "Cute Girls Doing Cute Things": Genres.cute_girls_doing_cute_things,
        "Gender Bending": Genres.gender_bender,
        "Ghost": Genres.ghost_story,
        "Harem": Genres.harem,
        "Historical": Genres.historical,
        "Isekai": Genres.isekai,
        "Iyashikei": Genres.iyashikei,
        "Mahjong": Genres.mahjong,
        "School": Genres.school,
        "Shoujo Ai": Genres.yuri,
        "Shounen Ai": Genres.yaoi,
        "Survival": Genres.survival,
        "Vampire": Genres.vampire,
        "Zombie": Genres.zombie,
        "Reverse Harem": Genres.harem,
        "Hentai": Genres.hentai,
    }

    demographic_mapping = {
        "Josei": Demographics.josei,
        "Seinen": Demographics.seinen,
        "Shounen": Demographics.shonen,
        "Shoujo": Demographics.shojo,
    }

    # Format: [2-digit ISO 3166-1 alpha-2 code]: (country name, language name)
    country_code_mapping: dict[str, tuple[pywikibot.ItemPage, pywikibot.ItemPage]] = {
        "JP": (japan_item, japanese_lang_item),
        "KR": (korea_item, korean_lang_item),
        "CN": (china_item, chinese_lang_item),
    }

    external_links_language_mapping: dict[str, pywikibot.ItemPage] = {
        "Japanese": japanese_lang_item,
        "Korean": korean_lang_item,
        "Chinese": chinese_lang_item,
    }

    language_to_iso_639_1 = {
        "ja": japanese_lang_item,
        "ko": korean_lang_item,
        "zh": chinese_lang_item,
    }

    def get(self, id: str, wikidata_item: pywikibot.ItemPage) -> Result:
        r = self.session.post(
            self.anilist_base, json={"query": self.query, "variables": {"id": id}}
        )
        r.raise_for_status()
        json = r.json()
        data = json["data"]["Media"]
        result = Result()
        if data["idMal"] is not None:
            claim = pywikibot.Claim(site, mal_id_prop)
            claim.setTarget(str(data["idMal"]))
            result.other_properties[mal_id_prop].append(ExtraProperty(claim=claim))
        if data["genres"] is not None:
            for genre in data["genres"]:
                if genre in self.genre_mapping:
                    result.genres.append(self.genre_mapping[genre])
        # Removing tags for now, they are user generated and not reliable.
        # if data["tags"] is not None:
        #     for tag in data["tags"]:
        #         if tag["name"] in self.genre_mapping:
        #             result.genres.append(self.genre_mapping[tag["name"]])
        if data["startDate"] is not None:
            result.start_date = SmartPrecisionTime(
                data["startDate"]["year"],
                data["startDate"]["month"],
                data["startDate"]["day"],
            )
        if data["endDate"] is not None and data["endDate"]["year"] is not None:
            result.end_date = SmartPrecisionTime(
                data["endDate"]["year"],
                data["endDate"]["month"],
                data["endDate"]["day"],
            )
        if data["chapters"] is not None:
            result.chapters = data["chapters"]
        if data["volumes"] is not None:
            result.volumes = data["volumes"]
        if data["countryOfOrigin"] is not None:
            if data["countryOfOrigin"] in self.country_code_mapping:
                country, language = self.country_code_mapping[data["countryOfOrigin"]]
                country_claim = pywikibot.Claim(site, country_prop)
                country_claim.setTarget(country)
                result.other_properties[country_prop].append(
                    ExtraProperty(claim=country_claim)
                )
                language_claim = pywikibot.Claim(site, language_prop)
                language_claim.setTarget(language)
                result.other_properties[language_prop].append(
                    ExtraProperty(claim=language_claim, skip_if_conflicting_exists=True)
                )
        if data["hashtag"] is not None:
            claim = pywikibot.Claim(site, hashtag_prop)
            claim.setTarget(data["hashtag"].lstrip("#").strip())
            result.other_properties[hashtag_prop].append(ExtraProperty(claim=claim))
        if data["externalLinks"] is not None:
            for item in data["externalLinks"]:
                if item["language"] in self.external_links_language_mapping:
                    result.links.append(
                        Link(
                            item["url"],
                            language=self.external_links_language_mapping[
                                item["language"]
                            ],
                        )
                    )
                else:
                    result.links.append(Link(item["url"]))
        if data["title"]:
            english = data["title"]["english"]
            native = data["title"]["native"]
            if english is not None:
                english_claim = pywikibot.Claim(site, title_prop)
                english_claim.setTarget(
                    pywikibot.WbMonolingualText(english.strip(), "en")
                )
                result.other_properties[title_prop].append(
                    ExtraProperty(
                        claim=english_claim, skip_if_conflicting_language_exists=True
                    )
                )
            if native is not None and language_prop in wikidata_item.claims and wikidata_item.claims[language_prop][0] in self.language_to_iso_639_1.values():  # type: ignore
                lang_item = wikidata_item.claims[language_prop][0]  # type: ignore
                lang_key = next(
                    key
                    for key, value in self.language_to_iso_639_1.items()
                    if value == lang_item
                )
                native_claim = pywikibot.Claim(site, title_prop)
                native_claim.setTarget(
                    pywikibot.WbMonolingualText(native.strip(), lang_key)
                )
                native_claim.setRank("preferred")
                result.other_properties[title_prop].append(
                    ExtraProperty(
                        claim=native_claim, skip_if_conflicting_language_exists=True
                    )
                )
        return result

    def compute_similar_reference(
        self, potential_ref: WikidataReference, id: str
    ) -> bool:
        if stated_at_prop in potential_ref:
            for claim in potential_ref[stated_at_prop]:
                if claim.getTarget().id == anilist_item.id:  # type: ignore
                    return True
        if url_prop in potential_ref:
            for claim in potential_ref[url_prop]:
                if f"https://anilist.co/manga/{id}" in claim.getTarget().lower():  # type: ignore
                    return True
        if anilist_id_prop in potential_ref:
            for claim in potential_ref[anilist_id_prop]:
                if claim.getTarget() == id:
                    return True
        return False

    def get_reference(self, id: str) -> Reference:
        return Reference(stated_in=anilist_item, url=f"https://anilist.co/manga/{id}")
