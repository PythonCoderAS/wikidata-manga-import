import dataclasses
import datetime
from collections import defaultdict
from typing import TYPE_CHECKING, Union

import pywikibot

from .extra_linkage import ExtraLinkageData

from ..constants import (
    Demographics,
    Genres,
    anime_news_network_prop,
    anime_news_network_regex,
    animeclick_prop,
    animeclick_regex,
    bgm_prop,
    bgm_regex,
    bookwalker_global_prop,
    bookwalker_prop,
    bookwalker_regex,
    demographic_prop,
    described_at_url_prop,
    ebookjapan_prop,
    ebookjapan_regex,
    end_prop,
    genre_prop,
    inkr_prop,
    inkr_regex,
    language_prop,
    media_arts_prop,
    media_arts_regex,
    niconico_prop,
    niconico_regex,
    num_parts_prop,
    site,
    start_prop,
    url_blacklist,
    volume_item,
)
from .bad_data import BadDataReport
from wikidata_bot_framework.dataclasses import (
    ExtraProperty,
    ExtraQualifier,
)
from wikidata_bot_framework.utils import (
    resolve_multiple_property_claims,
    get_entity_id_from_entity_url,
)
from .link import Link
from .smart_precision_time import SmartPrecisionTime

if TYPE_CHECKING:
    from ..abc.provider import Provider


def merge_nested_defaultdict[KO, KI, VI](
    dd1: defaultdict[KO, defaultdict[KI, set[VI]]],
    dd2: defaultdict[KO, defaultdict[KI, set[VI]]],
):
    """Merge two nested defaultdicts, putting the contents of dd2 into dd1."""
    for outer_key, inner_dict in dd2.items():
        for inner_key, value in inner_dict.items():
            dd1[outer_key][inner_key].update(value)


@dataclasses.dataclass
class Result:
    genres: list[Genres] = dataclasses.field(default_factory=list)
    demographics: list[Demographics] = dataclasses.field(default_factory=list)
    start_date: Union[datetime.datetime, pywikibot.WbTime, None] = None
    end_date: Union[datetime.datetime, pywikibot.WbTime, None] = None
    volumes: Union[int, None] = None
    chapters: Union[int, None] = None
    links: list[Link] = dataclasses.field(default_factory=list)

    other_properties: defaultdict[str, list[ExtraProperty]] = dataclasses.field(
        default_factory=lambda: defaultdict(list)
    )
    en_labels: set[str] = dataclasses.field(default_factory=set)

    bad_data_reports: list[BadDataReport] = dataclasses.field(default_factory=list)

    new_id: str | None = None  # Sets a new ID for use by references

    extra_item_linkings: defaultdict[
        str, defaultdict[str, list[ExtraLinkageData]]
    ] = dataclasses.field(
        default_factory=lambda: defaultdict(lambda: defaultdict(list))
    )
    """
    Easy way to conditionally add extra item links.

    For example, if you want to find all items where PXXX=YYY, and add a claim for PAAA=QBBB, you can do:

    .. code-block:: python

        result.extra_item_linkings["PAAA"]["PXXX"] = {"YYY"}
    """

    def simplify(self, provider: "Provider", provider_id: str):
        """Simplify the self to only have values in the other properties."""
        if self.genres:
            if Genres.romance in self.genres and Genres.comedy in self.genres:
                self.genres.append(Genres.romantic_comedy)
                self.genres.remove(Genres.romance)
                self.genres.remove(Genres.comedy)
            if Genres.comedy in self.genres and Genres.drama in self.genres:
                self.genres.append(Genres.comedy_drama)
                self.genres.remove(Genres.comedy)
                self.genres.remove(Genres.drama)
            for genre in set(self.genres):  # Dedupe
                genre_claim = pywikibot.Claim(site, genre_prop)
                genre_claim.setTarget(genre.value)
                self.other_properties[genre_prop].append(ExtraProperty(genre_claim))
        if self.demographics:
            for demographic in set(self.demographics):
                demographic_claim = pywikibot.Claim(site, demographic_prop)
                demographic_claim.setTarget(demographic.value)
                self.other_properties[demographic_prop].append(
                    ExtraProperty(demographic_claim)
                )
        if self.start_date:
            if isinstance(self.start_date, datetime.datetime):
                time_obj = SmartPrecisionTime(
                    year=self.start_date.year,
                    month=self.start_date.month,
                    day=self.start_date.day,
                )
            else:
                time_obj = self.start_date
            start_claim = pywikibot.Claim(site, start_prop)
            start_claim.setTarget(time_obj)
            self.other_properties[start_prop].append(ExtraProperty(start_claim))
        if self.end_date:
            if isinstance(self.end_date, datetime.datetime):
                time_obj = SmartPrecisionTime(
                    year=self.end_date.year,
                    month=self.end_date.month,
                    day=self.end_date.day,
                )
            else:
                time_obj = self.end_date
            end_claim = pywikibot.Claim(site, end_prop)
            end_claim.setTarget(time_obj)
            self.other_properties[end_prop].append(ExtraProperty(end_claim))
        if self.volumes:
            quantity = pywikibot.WbQuantity(self.volumes, volume_item, site=site)
            num_parts_claim = pywikibot.Claim(site, num_parts_prop)
            num_parts_claim.setTarget(quantity)
            self.other_properties[num_parts_prop].append(ExtraProperty(num_parts_claim))
        self.simplify_links()
        self.simplify_extra_linkings(provider, provider_id)

    def simplify_links(self):
        for link in self.links:
            url = link.url
            if match := niconico_regex.search(url):
                niconico_id = match.group(1)
                niconico_claim = pywikibot.Claim(site, niconico_prop)
                niconico_claim.setTarget(f"comic/{niconico_id}")
                self.other_properties[niconico_prop].append(
                    ExtraProperty(niconico_claim)
                )
            elif match := bookwalker_regex.search(url):
                prop_to_use = (
                    bookwalker_global_prop
                    if "global.bookwalker" in url
                    else bookwalker_prop
                )
                bookwalker_id = match.group(1)
                bookwalker_claim = pywikibot.Claim(site, prop_to_use)
                bookwalker_claim.setTarget(bookwalker_id)
                self.other_properties[prop_to_use].append(
                    ExtraProperty(bookwalker_claim)
                )
            elif match := inkr_regex.search(url):
                inkr_id = match.group(1)
                inkr_claim = pywikibot.Claim(site, inkr_prop)
                inkr_claim.setTarget(inkr_id)
                self.other_properties[inkr_prop].append(ExtraProperty(inkr_claim))
            elif match := anime_news_network_regex.search(url):
                anime_news_network_id = match.group(1)
                anime_news_network_claim = pywikibot.Claim(
                    site, anime_news_network_prop
                )
                anime_news_network_claim.setTarget(anime_news_network_id)
                self.other_properties[anime_news_network_prop].append(
                    ExtraProperty(anime_news_network_claim)
                )
            elif match := media_arts_regex.search(url):
                media_arts_id = match.group(1)
                media_arts_claim = pywikibot.Claim(site, media_arts_prop)
                media_arts_claim.setTarget(f"C{media_arts_id}")
                self.other_properties[media_arts_prop].append(
                    ExtraProperty(media_arts_claim)
                )
            elif match := bgm_regex.search(url):
                bgm_id = match.group(1)
                bgm_claim = pywikibot.Claim(site, bgm_prop)
                bgm_claim.setTarget(bgm_id)
                self.other_properties[bgm_prop].append(ExtraProperty(bgm_claim))
            elif match := animeclick_regex.search(url):
                animeclick_id = match.group(1)
                animeclick_claim = pywikibot.Claim(site, animeclick_prop)
                animeclick_claim.setTarget(animeclick_id)
                self.other_properties[animeclick_prop].append(
                    ExtraProperty(animeclick_claim)
                )
            elif match := ebookjapan_regex.search(url):
                ebookjapan_id = match.group(1)
                ebookjapan_claim = pywikibot.Claim(site, ebookjapan_prop)
                ebookjapan_claim.setTarget(ebookjapan_id)
                self.other_properties[ebookjapan_prop].append(
                    ExtraProperty(ebookjapan_claim)
                )
            else:
                if any(
                    (
                        (blacklisted_url in url)
                        if isinstance(blacklisted_url, str)
                        else (blacklisted_url.search(url))
                    )
                    for blacklisted_url in url_blacklist
                ):
                    continue
                url_claim = pywikibot.Claim(site, described_at_url_prop)
                url_claim.setTarget(url)
                extra_prop = ExtraProperty(url_claim)
                self.other_properties[described_at_url_prop].append(extra_prop)
                if link.language:
                    language_claim = pywikibot.Claim(site, language_prop)
                    language_claim.setTarget(link.language)
                    extra_prop.qualifiers[language_prop].append(
                        ExtraQualifier(language_claim, skip_if_conflicting_exists=True)
                    )

    def simplify_extra_linkings(self, provider: "Provider", provider_id: str):
        true_resolution_data: defaultdict[
            str, defaultdict[str, set[str]]
        ] = defaultdict(lambda: defaultdict(set))
        for target_prop, resolution_data in self.extra_item_linkings.items():
            for resolution_prop, resolution_values in resolution_data.items():
                for resolution_value in resolution_values:
                    true_resolution_data[target_prop][resolution_prop].add(
                        resolution_value.value
                    )
                    merge_nested_defaultdict(
                        true_resolution_data, resolution_value.qualifiers_to_resolve
                    )

        final_dictionary: defaultdict[str, set[str]] = defaultdict(set)
        for resolution_key, resolution_values in true_resolution_data.values():
            final_dictionary[resolution_key].update(resolution_values)
        results = resolve_multiple_property_claims(final_dictionary)
        for target_prop, resolution_data in self.extra_item_linkings.items():
            for resolution_prop, resolution_values in resolution_data.items():
                for resolution_value in resolution_values:
                    resolved_pair = results.get(
                        (resolution_prop, resolution_value.value), None
                    )
                    if not resolved_pair:
                        continue
                    if len(resolved_pair) > 1 and not resolution_value.allow_duplicates:
                        self.bad_data_reports.append(
                            BadDataReport.from_duplicate_extra_item_linkage(
                                provider,
                                provider_id,
                                resolution_prop,
                                resolution_value.value,
                                list(resolved_pair),
                            )
                        )
                    else:
                        for resolved_value in resolved_pair:
                            extra_prop = ExtraProperty.from_property_id_and_value(
                                target_prop,
                                get_entity_id_from_entity_url(resolved_value),
                            )
                            extra_prop.add_qualifiers(
                                resolution_value.resolved_qualifiers
                            )
                            found_all_qualifiers = True
                            for (
                                qualifier_target_prop,
                                qualifier_resolution_data,
                            ) in resolution_value.qualifiers_to_resolve.items():
                                for (
                                    qualifier_resolution_prop,
                                    qualifier_resolution_values,
                                ) in qualifier_resolution_data.items():
                                    for (
                                        qualifier_resolution_value
                                    ) in qualifier_resolution_values:
                                        resolved_qualifier_pair = results.get(
                                            (
                                                qualifier_resolution_prop,
                                                qualifier_resolution_value,
                                            ),
                                            None,
                                        )
                                        if (
                                            not found_all_qualifiers
                                            and resolution_value.require_qualifiers_for_placement
                                        ):
                                            break
                                        if not resolved_qualifier_pair:
                                            found_all_qualifiers = False
                                            continue
                                        elif (
                                            len(resolved_qualifier_pair) > 1
                                            and not resolution_value.allow_duplicates
                                        ):
                                            self.bad_data_reports.append(
                                                BadDataReport.from_duplicate_extra_item_linkage(
                                                    provider,
                                                    provider_id,
                                                    qualifier_resolution_prop,
                                                    qualifier_resolution_value,
                                                    list(resolved_qualifier_pair),
                                                )
                                            )
                                        else:
                                            for (
                                                resolved_qualifier_value
                                            ) in resolved_qualifier_pair:
                                                extra_prop.add_qualifier(
                                                    ExtraQualifier.from_property_id_and_value(
                                                        qualifier_target_prop,
                                                        get_entity_id_from_entity_url(
                                                            resolved_qualifier_value
                                                        ),
                                                    )
                                                )
                                    if (
                                        not found_all_qualifiers
                                        and resolution_value.require_qualifiers_for_placement
                                    ):
                                        break
                                if (
                                    not found_all_qualifiers
                                    and resolution_value.require_qualifiers_for_placement
                                ):
                                    break
                            if (
                                not found_all_qualifiers
                                and resolution_value.require_qualifiers_for_placement
                            ):
                                continue
                            self.other_properties[target_prop].append(extra_prop)
