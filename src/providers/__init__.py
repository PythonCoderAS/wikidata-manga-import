from ..abc.provider import Provider
from ..constants import (
    anilist_id_prop,
    anime_planet_prop,
    inkr_prop,
    kitsu_prop,
    mal_id_prop,
    md_id_prop,
    mu_id_prop,
)
from .anilist import AnilistProvider
from .anime_planet.provider import AnimePlanetProvider
from .inkr.provider import INKRProvider
from .kitsu import KitsuProvider
from .mal import MALProvider
from .md import MangadexProvider
from .mu import MangaUpdatesProvider

# Key should be the property number that contains the provider ID.
providers: dict[str, Provider] = {
    mal_id_prop: MALProvider(),
    anilist_id_prop: AnilistProvider(),
    md_id_prop: MangadexProvider(),
    mu_id_prop: MangaUpdatesProvider(),
    anime_planet_prop: AnimePlanetProvider(),
    inkr_prop: INKRProvider(),
    kitsu_prop: KitsuProvider(),
}
