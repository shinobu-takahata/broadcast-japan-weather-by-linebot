import requests

from infrastructure.exceptions import GeocodingAPIException, GeocodingNotFoundException
from utils.retry import retry


class GeocodingClient:
    """OpenWeatherMap Geocoding APIクライアント"""

    BASE_URL = "https://api.openweathermap.org/geo/1.0"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @retry(max_attempts=3, backoff=[1, 2, 4])
    def get_coordinates(self, city_name: str) -> tuple[float, float, str]:
        """市区町村名から緯度経度を取得

        Returns:
            (latitude, longitude, city_name_ja)

        Raises:
            GeocodingNotFoundException: 地名が見つからない
            GeocodingAPIException: APIエラー
        """
        url = f"{self.BASE_URL}/direct"
        params = {
            "q": f"{city_name},JP",
            "limit": 1,
            "appid": self.api_key,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise GeocodingAPIException(f"Geocoding API HTTPエラー: {e}") from e
        except requests.exceptions.RequestException as e:
            raise GeocodingAPIException(f"Geocoding API通信エラー: {e}") from e

        data = response.json()
        if not data:
            raise GeocodingNotFoundException(f"地名が見つかりません: {city_name}")

        location = data[0]
        display_name = location.get("local_names", {}).get("ja", city_name)
        return (location["lat"], location["lon"], display_name)
