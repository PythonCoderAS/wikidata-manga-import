from collections import defaultdict
import dataclasses

from wikidata_bot_framework.dataclasses import ExtraQualifier


@dataclasses.dataclass(frozen=True)
class ExtraLinkageQualifierData:
    value: str
    allow_duplicates: bool = False


@dataclasses.dataclass(unsafe_hash=True)
class ExtraLinkageData:
    value: str = dataclasses.field(hash=True)
    resolved_qualifiers: list[ExtraQualifier] = dataclasses.field(
        default_factory=list, compare=False, hash=False
    )
    qualifiers_to_resolve: defaultdict[
        str, defaultdict[str, set[str]]
    ] = dataclasses.field(
        default_factory=lambda: defaultdict(lambda: defaultdict(set)),
        compare=False,
        hash=False,
    )
    require_qualifiers_for_placement: bool = dataclasses.field(
        default=False, compare=False, hash=False
    )
    allow_duplicates: bool = dataclasses.field(default=False, compare=False, hash=False)
    """
    Set to true (default) to make a bad data report when multiple items are found for one PXXX=YYY.

    Set to false to add multiple items.
    """
