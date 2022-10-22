from ..constants import mal_id_prop, anilist_id_prop
from .anilist import AnilistProvider
from .mal import MALProvider


# Key should be the property number that contains the provider ID.
providers = {
    mal_id_prop: MALProvider(),
    anilist_id_prop: AnilistProvider()
}