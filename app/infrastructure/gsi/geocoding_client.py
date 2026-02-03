import re

import requests

from infrastructure.exceptions import (
    GeocodingAmbiguousException,
    GeocodingAPIException,
    GeocodingNotFoundException,
)
from utils.retry import retry

CITY_PATTERN = re.compile(r"^.+[都道府県].+[市区町村郡]")


class GsiGeocodingClient:
    """国土地理院 住所検索APIクライアント"""

    BASE_URL = "https://msearch.gsi.go.jp/address-search/AddressSearch"

    @retry(max_attempts=3, backoff=[1, 2, 4])
    def get_coordinates(self, city_name: str) -> tuple[float, float, str]:
        """市区町村名から緯度経度を取得

        Returns:
            (latitude, longitude, city_name_ja)

        Raises:
            GeocodingNotFoundException: 地名が見つからない
            GeocodingAmbiguousException: 複数の候補がある
            GeocodingAPIException: APIエラー
        """
        params = {"q": city_name}

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise GeocodingAPIException(f"GSI API HTTPエラー: {e}") from e
        except requests.exceptions.RequestException as e:
            raise GeocodingAPIException(f"GSI API通信エラー: {e}") from e

        features = response.json()

        candidates = []
        for feature in features:
            title = feature.get("properties", {}).get("title", "")
            if CITY_PATTERN.match(title):
                coords = feature["geometry"]["coordinates"]
                candidates.append((coords[1], coords[0], title))

        if len(candidates) == 0:
            raise GeocodingNotFoundException(f"地名が見つかりません: {city_name}")

        if len(candidates) == 1:
            return candidates[0]

        # 複数候補 - 末尾が市区町村で終わらないものを除外
        filtered = [c for c in candidates if c[2].endswith(("市", "区", "町", "村"))]
        if len(filtered) > 0:
            candidates = filtered

        # 重複タイトルを除去して再チェック
        seen = set()
        unique = []
        for c in candidates:
            if c[2] not in seen:
                seen.add(c[2])
                unique.append(c)

        if len(unique) == 1:
            return unique[0]

        raise GeocodingAmbiguousException(
            f"複数の候補があります: {city_name}",
            candidates=[c[2] for c in unique],
        )
