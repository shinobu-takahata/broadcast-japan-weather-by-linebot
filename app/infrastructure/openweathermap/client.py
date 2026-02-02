import requests

from infrastructure.exceptions import WeatherAPIException
from utils.retry import retry


class OpenWeatherMapClient:
    """OpenWeatherMap 5 Day / 3 Hour Forecast API クライアント"""

    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @retry(max_attempts=3, backoff=[1, 2, 4])
    def get_hourly_weather(self, lat: float, lon: float) -> list[dict]:
        """指定した緯度経度の3時間ごとの天気情報を取得

        Args:
            lat: 緯度
            lon: 経度

        Returns:
            天気データのリスト（各要素: dt, temp）

        Raises:
            WeatherAPIException: API呼び出しエラー
        """
        params = {
            "lat": lat,
            "lon": lon,
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
        # Forecast APIのレスポンス形式をWeatherCalculatorが期待する形式に正規化
        return [
            {"dt": entry["dt"], "temp": entry["main"]["temp"]}
            for entry in data.get("list", [])
        ]
