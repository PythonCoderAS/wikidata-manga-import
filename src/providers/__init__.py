from ..abc.provider import Provider
from .mal import MALProvider


# Key should be the property number that contains the provider ID.
providers = {
    "P4087": MALProvider(),
}