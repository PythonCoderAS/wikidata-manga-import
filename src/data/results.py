from collections import defaultdict

import dataclasses
import datetime

import pywikibot

from ..data.smart_precision_time import SmartPrecisionTime
from ..data.link import Link

from .extra_property import ExtraProperty, ExtraQualifier
from ..constants import Genres, Demographics, genre_prop, site, demographic_prop, start_prop, num_parts_prop, volume_item, niconico_regex, bookwalker_regex, bookwalker_prop, niconico_prop, described_at_url_prop, language_prop, url_blacklist

@dataclasses.dataclass
class Result:
    genres: list[Genres] = dataclasses.field(default_factory=list)
    demographics: list[Demographics] = dataclasses.field(default_factory=list)
    start_date: datetime.datetime| pywikibot.WbTime | None = None
    end_date: datetime.datetime | pywikibot.WbTime | None = None
    volumes: int | None = None
    chapters: int | None = None
    links: list[Link] = dataclasses.field(default_factory=list)
    
    other_properties: defaultdict[str, list[ExtraProperty]] = dataclasses.field(default_factory=lambda: defaultdict(list))
    en_labels: set[str] = dataclasses.field(default_factory=set)

    def simplify(self):
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
            for genre in self.genres:
                genre_claim = pywikibot.Claim(site, genre_prop)
                genre_claim.setTarget(genre.value)
                self.other_properties[genre_prop].append(ExtraProperty(genre_claim))
        if self.demographics:
            for demographic in self.demographics:
                demographic_claim = pywikibot.Claim(site, demographic_prop)
                demographic_claim.setTarget(demographic.value)
                self.other_properties[demographic_prop].append(ExtraProperty(demographic_claim))
        if self.start_date:
            if isinstance(self.start_date, datetime.datetime):
                time_obj = SmartPrecisionTime(year=self.start_date.year, month=self.start_date.month, day=self.start_date.day)
            else:
                time_obj = self.start_date
            start_claim = pywikibot.Claim(site, start_prop)
            start_claim.setTarget(time_obj)
            self.other_properties[start_prop].append(ExtraProperty(start_claim))
        if self.volumes:
            quantity = pywikibot.WbQuantity(self.volumes, volume_item, site=site)
            num_parts_claim = pywikibot.Claim(site, num_parts_prop)
            num_parts_claim.setTarget(quantity)
            self.other_properties[num_parts_prop].append(ExtraProperty(num_parts_claim))
        for link in self.links:
            url = link.url
            if match := niconico_regex.search(url):
                niconico_id = match.group(1)
                niconico_claim = pywikibot.Claim(site, niconico_prop)
                niconico_claim.setTarget(f"comic/{niconico_id}")
                self.other_properties[niconico_prop].append(ExtraProperty(niconico_claim))
            elif match := "global.bookwalker.jp" not in url and bookwalker_regex.search(url):
                bookwalker_id = match.group(1)
                bookwalker_claim = pywikibot.Claim(site, bookwalker_prop)
                bookwalker_claim.setTarget(bookwalker_id)
                self.other_properties[bookwalker_prop].append(ExtraProperty(bookwalker_claim))
            else:
                if any(((blacklisted_url in url) if isinstance(blacklisted_url, str) else (blacklisted_url.search(url))) for blacklisted_url in url_blacklist):
                    continue
                url_claim = pywikibot.Claim(site, described_at_url_prop)
                url_claim.setTarget(url)
                extra_prop = ExtraProperty(url_claim)
                self.other_properties[described_at_url_prop].append(extra_prop)
                if link.language:
                    language_claim = pywikibot.Claim(site, language_prop)
                    language_claim.setTarget(link.language)
                    extra_prop.qualifiers[language_prop].append(ExtraQualifier(language_claim, skip_if_conflicting_exists=True))