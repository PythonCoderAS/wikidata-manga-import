import dataclasses

@dataclasses.dataclass
class ProviderResults:
    """Signals if some net change occured due to the provider's run."""
    properties_added: int = 0
    qualifiers_added: int = 0
    references_added: int = 0
    ranks_modified: int = 0

    def changed(self) -> bool:
        """Return True if some net change occured."""
        return any((self.properties_added, self.qualifiers_added, self.references_added, self.ranks_modified))