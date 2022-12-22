from abc import ABC, abstractmethod

import pywikibot

from ..constants import session as requests_session
from ..data.reference import Reference
from ..data.results import Result
from ..pywikibot_stub_types import WikidataReference


class Provider(ABC):
    name: str
    session = requests_session

    @abstractmethod
    def get(self, id: str, item: pywikibot.ItemPage) -> Result:
        """Gets the list of results for a given provider ID.

        Note: May be expanded to return more than just those

        Args:
            id (str): The provider ID.
            item (pywikibot.ItemPage): The existing Wikidata item.

        Returns:
            Result: The results to given.
        """
        raise NotImplementedError

    @abstractmethod
    def compute_similar_reference(
        self, potential_ref: WikidataReference, id: str
    ) -> bool:
        """Computes whether a given reference can be counted as .

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
