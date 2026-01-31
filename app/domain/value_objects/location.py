from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    """地域情報の値オブジェクト"""

    city_name: str
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not self.city_name:
            raise ValueError("市区町村名は必須です")
        if not -90 <= self.latitude <= 90:
            raise ValueError("緯度は-90〜90の範囲である必要があります")
        if not -180 <= self.longitude <= 180:
            raise ValueError("経度は-180〜180の範囲である必要があります")
