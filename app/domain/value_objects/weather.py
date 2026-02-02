from dataclasses import dataclass


@dataclass(frozen=True)
class Weather:
    """実質天気情報（9:00〜23:00 JST）"""

    max_temp: float
    min_temp: float
    pop: int

    def __post_init__(self) -> None:
        if not 0 <= self.pop <= 100:
            raise ValueError("降水確率は0〜100の範囲である必要があります")
        if self.max_temp < self.min_temp:
            raise ValueError("最高気温は最低気温以上である必要があります")
