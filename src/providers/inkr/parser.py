import re

from ...constants import inkr_prop
from . import ParserResult

base_url = "https://comics.inkr.com/title"
genre_url_regex = re.compile(r"https://comics\.inkr\.com/genre/(\d+)", re.IGNORECASE)


def get_data(id: str) -> ParserResult:
    from .. import providers

    r, _ = providers[inkr_prop].do_request_with_retries(
        "GET",
        f"{base_url}/{id}",
        return_json=False,
        on_retry_limit_exhaused_exception="raise",
        not_found_on_request_404=True,
    )
    if r is None:
        return ParserResult()
    text = r.text
    genres = genre_url_regex.findall(text)
    return ParserResult(genres=genres)
