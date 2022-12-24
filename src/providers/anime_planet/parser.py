import re
from typing import List

from bs4 import BeautifulSoup, Tag

from . import ParserResult
from ...constants import session

base_url = "https://www.anime-planet.com/manga"
magazine_url_regex = re.compile(r"/manga/magazines/([a-z-]+)", re.IGNORECASE)
tag_url_regex = re.compile(r"/manga/tags/([a-z-]+)", re.IGNORECASE)


def get_data(manga_id: str) -> ParserResult:
    r = session.get(f"{base_url}/{manga_id}")
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    result = ParserResult()
    section = soup.find(attrs={"id": "siteContainer"}).find("section")
    divs: List[Tag] = section.find_all("div", recursive=False)
    vol_and_chap_info, magazine_info, year_info, = divs[0], divs[1], divs[2]

    # Volumes and chapters
    vol_and_chap_string = vol_and_chap_info.text.strip()
    if "; " in vol_and_chap_string:
        # Contains both volume and chapter in that order
        parts = vol_and_chap_string.split("; ")
    else:
        # Contains chapter only
        parts = [vol_and_chap_string]
    for part in parts:
        label, _, value = part.partition(": ")
        if "+" not in value:
            # If there is a plus, it means the manga is not complete.
            if label == "Vol":
                result.volumes = int(value)
            elif label == "Ch":
                result.chapters = int(value)

    # Magazine external IDs
    for a in magazine_info.find_all("a", recursive=False):
        a: Tag
        if match := magazine_url_regex.search(a["href"]):
            result.magazine.append(match.group(1))

    # Parsing start/end year
    years_string = year_info.find("span", {"class": "iconYear"}).text.strip()
    if " - " in years_string:
        # Has a range, so the first part is the start year.
        start_year, _, end_year = years_string.partition(" - ")
        result.start_year = int(start_year)
        # ? means that it hasn't ended yet.
        if end_year != "?":
            result.end_year = int(end_year)
    else:
        # Start and end year are the same
        result.start_year = result.end_year = int(years_string)

    # Parsing tags
    for a in soup.find("div", {"class": "tags"}).find_all("a", recursive=True):
        a: Tag
        if match := tag_url_regex.search(a["href"]):
            result.tags.append(match.group(1))

    return result
