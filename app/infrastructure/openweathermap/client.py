import requests

from infrastructure.exceptions import WeatherAPIException
from utils.retry import retry


class OpenWeatherMapClient:
    """OpenWeatherMap One Call API 3.0 クライアント"""

    BASE_URL = "https://api.openweathermap.org/data/3.0/onecall"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @retry(max_attempts=3, backoff=[1, 2, 4])
    def get_hourly_weather(self, lat: float, lon: float) -> list[dict]:
        """指定した緯度経度の時間ごとの天気情報を取得

        Args:
            lat: 緯度
            lon: 経度

        Returns:
            hourlyデータのリスト（各要素: dt, temp, pop）

        Raises:
            WeatherAPIException: API呼び出しエラー
        """
        params = {
            "lat": lat,
            "lon": lon,
            "exclude": "minutely,alerts",
            "units": "metric",
            "lang": "ja",
            "appid": self.api_key,
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise WeatherAPIException(f"OpenWeatherMap API呼び出しエラー: {e}") from e

        data = response.json()
        return data.get("hourly", [])
