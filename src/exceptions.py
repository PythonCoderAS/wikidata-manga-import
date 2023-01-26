class NotFoundException(Exception):
    """Used to denote that the given identifier was not found in the provider."""


class AbortError(Exception):
    """Used to hit an except block."""
