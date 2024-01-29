from abc import ABC, abstractmethod
import time
from typing import Any, Literal, Union

from requests import Response
import requests
from wikidata_bot_framework import EntityPage, Output

from ..constants import session as requests_session, spoofed_chrome_user_agent
from ..data.reference import Reference
from ..data.results import Result
from ..exceptions import NotFoundException
from ..pywikibot_stub_types import WikidataReference

_JSONType = Union[str, int, float, bool, list[Any], dict[str, Any]]


class Provider(ABC):
    name: str
    prop: str
    session = requests_session

    @abstractmethod
    def get(self, id: str, item: EntityPage) -> Result:
        """Gets the list of results for a given provider ID.

        Note: May be expanded to return more than just those

        Args:
            id (str): The provider ID.
            item (EntityPage): The existing Wikidata item.

        Returns:
            Result: The results to given.
        """
        raise NotImplementedError

    @abstractmethod
    def compute_similar_reference(
        self, potential_ref: WikidataReference, id: str
    ) -> bool:
        """Computes whether a given reference can be counted as a reference to the provider.

        Args:
            potential_ref (WikidataReference): The reference to compare.
            id (str): The provider ID.

        Returns:
            bool: Whether the reference is similar.
        """
        raise NotImplementedError

    @abstractmethod
    def get_reference(self, id: str) -> Reference:
        """Gets the reference for a given provider ID.

        Args:
            id (str): The provider ID.

        Returns:
            Reference: The reference to given.
        """
        raise NotImplementedError

    def post_process_hook(self, output: Output, item: EntityPage) -> bool:
        """Runs after the item has been edited.

        This should be used to do any post-processing, such as replacing/deleting claims.

        Args:
            item (EntityPage): The item that was edited.

        Returns:
            bool: Whether the item has been edited.
        """
        return False

    # Provider utilities. They should mostly be staticmethods

    @staticmethod
    def not_found_on_request_404(r: Response):
        """Throws a NotFoundException if the request returns a 404.

        Args:
            r (Response): The response to check.

        Raises:
            NotFoundException: If the response is a 404.

        Returns:
            None: If the response is not a 404.
        """
        if r.status_code == 404:
            raise NotFoundException(r)

    def do_request_with_retries(
        self,
        method: str,
        url: str,
        *,
        retries: int = 3,
        sleep_time_between_retries: float = 5,
        retry_on_status_codes: tuple[int, ...] = tuple(),
        retry_on_status_code_range: tuple[int, ...] = (5,),
        retry_on_exceptions: tuple[type[Exception], ...] = (
            requests.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ContentDecodingError,
        ),
        on_retry_limit_exhuasted_status_code: Literal[
            "raise", "ignore", "return_none"
        ] = "return_none",
        on_other_bad_status_code: Literal["raise", "ignore", "return_none"] = "raise",
        not_found_on_request_404: bool = False,
        on_retry_limit_exhaused_exception: Literal[
            "raise", "return_none"
        ] = "return_none",
        return_json: bool = True,
        retry_on_json_exceptions: tuple[type[Exception], ...] = (
            requests.JSONDecodeError,
        ),
        on_retry_limit_exhuasted_json_exception: Literal[
            "raise", "return_none"
        ] = "return_none",
        use_spoofed_user_agent: bool = False,
        use_exponential_backoff: bool = False,
        **kwargs,
    ) -> tuple[Union[requests.Response, None], Union[_JSONType, None]]:
        headers = {}
        if use_spoofed_user_agent:
            headers = {"User-Agent": spoofed_chrome_user_agent}
        recursive_kwargs = dict(
            method=method,
            url=url,
            retries=retries - 1,
            sleep_time_between_retries=sleep_time_between_retries,
            retry_on_status_codes=retry_on_status_codes,
            retry_on_status_code_range=retry_on_status_code_range,
            retry_on_exceptions=retry_on_exceptions,
            on_retry_limit_exhuasted_status_code=on_retry_limit_exhuasted_status_code,
            on_other_bad_status_code=on_other_bad_status_code,
            not_found_on_request_404=not_found_on_request_404,
            on_retry_limit_exhaused_exception=on_retry_limit_exhaused_exception,
            return_json=return_json,
            retry_on_json_exceptions=retry_on_json_exceptions,
            on_retry_limit_exhuasted_json_exception=on_retry_limit_exhuasted_json_exception,
            use_spoofed_user_agent=use_spoofed_user_agent,
            use_exponential_backoff=use_exponential_backoff,
            **kwargs,
        )
        true_sleep_time = (
            sleep_time_between_retries * pow(2, 3 - retries)
            if use_exponential_backoff
            else sleep_time_between_retries
        )
        try:
            r = self.session.request(method, url, headers=headers, **kwargs)
        except retry_on_exceptions:
            if retries == 0:
                if on_retry_limit_exhaused_exception == "return_none":
                    return None, None
                elif on_retry_limit_exhaused_exception == "raise":
                    raise
            else:
                time.sleep(true_sleep_time)
                return self.do_request_with_retries(**recursive_kwargs)
        status = r.status_code
        if status in retry_on_status_codes:
            if retries == 0:
                if on_retry_limit_exhuasted_status_code == "return_none":
                    return None, None
                elif on_retry_limit_exhuasted_status_code == "raise":
                    r.raise_for_status()
                elif on_retry_limit_exhuasted_status_code == "ignore":
                    pass
            else:
                time.sleep(true_sleep_time)
                return self.do_request_with_retries(**recursive_kwargs)
        elif not_found_on_request_404 and status == 404:
            raise NotFoundException(r)
        elif status // 100 in retry_on_status_code_range:
            if retries == 0:
                if on_retry_limit_exhuasted_status_code == "return_none":
                    return None, None
                elif on_retry_limit_exhuasted_status_code == "raise":
                    r.raise_for_status()
                elif on_retry_limit_exhuasted_status_code == "ignore":
                    pass
            else:
                time.sleep(true_sleep_time)
                return self.do_request_with_retries(**recursive_kwargs)
        elif status // 100 > 3:
            if on_other_bad_status_code == "return_none":
                return None, None
            elif on_other_bad_status_code == "raise":
                r.raise_for_status()
            elif on_other_bad_status_code == "ignore":
                pass
        if return_json:
            try:
                return r, r.json()
            except retry_on_json_exceptions:
                if retries == 0:
                    if on_retry_limit_exhuasted_json_exception == "return_none":
                        return r, None
                    elif on_retry_limit_exhuasted_json_exception == "raise":
                        raise
                else:
                    time.sleep(true_sleep_time)
                    return self.do_request_with_retries(**recursive_kwargs)
        else:
            return r, None
