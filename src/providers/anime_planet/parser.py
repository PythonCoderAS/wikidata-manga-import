import re
from typing import List

from bs4 import BeautifulSoup, Tag

from ...exceptions import NotFoundException
from ...constants import anime_planet_prop
from . import ParserResult

base_url = "https://www.anime-planet.com/manga"
magazine_url_regex = re.compile(r"/manga/magazines/([a-z-]+)", re.IGNORECASE)
tag_url_regex = re.compile(r"/manga/tags/([a-z-]+)", re.IGNORECASE)
ap_new_url_regex = re.compile(rf"{base_url}/([a-z\d-]+)", re.IGNORECASE)


def get_data(manga_id: str) -> ParserResult:
    from .. import providers

    r, _ = providers[anime_planet_prop].do_request_with_retries(
        "GET",
        f"{base_url}/{manga_id}",
        on_retry_limit_exhaused_exception="raise",
        return_json=False,
        use_spoofed_user_agent=True,
        on_other_bad_status_code="ignore",
    )
    if r is None:
        return ParserResult()
    if r.status_code == 404:
        data = {"ap_id": manga_id, "history": []}
        if r.history:
            data["history"] = [h.url for h in r.history]
        raise NotFoundException(data)
    else:
        r.raise_for_status()
    new_manga_id = ap_new_url_regex.search(r.url).group(1)
    result = ParserResult(new_id=new_manga_id)
    for item in r.history:
        result.previous_ids.append(ap_new_url_regex.search(item.url).group(1))
    soup = BeautifulSoup(r.text, "html.parser")
    section = soup.find(attrs={"id": "siteContainer"}).find("section")
    assert section is not None
    divs: List[Tag] = section.find_all("div", recursive=False)
    (
        vol_and_chap_info,
        magazine_info,
        year_info,
    ) = (
        divs[0],
        divs[1],
        divs[2],
    )

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
