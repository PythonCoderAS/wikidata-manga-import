import dataclasses


@dataclasses.dataclass
class ParserResult:
    genres: list[int] = dataclasses.field(default_factory=list)
