import re

from ...abc.provider import Provider
from ...constants import session
from . import ParserResult

base_url = "https://comics.inkr.com/title"
genre_url_regex = re.compile(r"https://comics\.inkr\.com/genre/(\d+)", re.IGNORECASE)


def get_data(id: str) -> ParserResult:
    r = session.get(f"{base_url}/{id}")
    Provider.not_found_on_request_404(r)
    r.raise_for_status()
    text = r.text
    genres = genre_url_regex.findall(text)
    return ParserResult(genres=genres)
