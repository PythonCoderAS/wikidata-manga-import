from abc import ABC, abstractmethod

from requests import Response
from wikidata_bot_framework import EntityPage, Output

from ..constants import session as requests_session
from ..data.reference import Reference
from ..data.results import Result
from ..exceptions import NotFoundException
from ..pywikibot_stub_types import WikidataReference


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

    # Provider utilities. They should all be staticmethods
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
