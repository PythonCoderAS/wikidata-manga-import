import dataclasses

@dataclasses.dataclass
class ProviderResults:
    """Signals if some net change occurred due to the provider's run."""
    properties_added: int = 0
    qualifiers_added: int = 0

    def changed(self) -> bool:
        """Return True if some net change occurred."""
        return any((self.properties_added, self.qualifiers_added))
