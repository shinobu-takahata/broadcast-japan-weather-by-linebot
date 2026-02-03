import requests

from infrastructure.exceptions import WeatherAPIException
from utils.retry import retry


class WeatherApiClient:
    """WeatherAPI (weatherapi.com) Forecast API クライアント"""

    BASE_URL = "https://api.weatherapi.com/v1/forecast.json"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @retry(max_attempts=3, backoff=[1, 2, 4])
    def get_hourly_weather(self, lat: float, lon: float) -> list[dict]:
        """指定した緯度経度の1時間ごとの天気情報を取得

        Args:
            lat: 緯度
            lon: 経度

        Returns:
            天気データのリスト（各要素: time, temp）

        Raises:
            WeatherAPIException: API呼び出しエラー
        """
        params = {
            "key": self.api_key,
            "q": f"{lat},{lon}",
            "days": 1,
            "lang": "ja",
            "aqi": "no",
            "alerts": "no",
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise WeatherAPIException(f"WeatherAPI 呼び出しエラー: {e}") from e

        data = response.json()
        today = data.get("forecast", {}).get("forecastday", [])
        if not today:
            return []

        return [{"time": hour["time"], "temp": hour["temp_c"]} for hour in today[0].get("hour", [])]
