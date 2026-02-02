import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from domain.value_objects.weather import Weather

JST = ZoneInfo("Asia/Tokyo")
HOUR_START = 9
HOUR_END = 23


class WeatherCalculator:
    """実質天気（9:00〜23:00 JST）を算出するドメインサービス"""

    def calculate(self, hourly_data: list[dict]) -> Weather:
        """hourlyデータから実質天気を算出する

        Args:
            hourly_data: OpenWeatherMap APIのhourly配列。各要素は dt, temp, pop を持つ。

        Returns:
            Weather: 実質天気情報

        Raises:
            ValueError: 対象時間帯のデータが存在しない場合
        """
        filtered = []
        for entry in hourly_data:
            dt_utc = datetime.fromtimestamp(entry["dt"], tz=timezone.utc)
            dt_jst = dt_utc.astimezone(JST)
            if HOUR_START <= dt_jst.hour < HOUR_END:
                filtered.append(entry)

        if not filtered:
            raise ValueError("9:00〜23:00（JST）の天気データが存在しません")

        temps = [entry["temp"] for entry in filtered]
        pops = [entry["pop"] for entry in filtered]

        max_temp = round(max(temps), 1)
        min_temp = round(min(temps), 1)
        pop = math.floor(max(pops) * 100)

        return Weather(max_temp=max_temp, min_temp=min_temp, pop=pop)
