from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from domain.value_objects.weather import Weather

JST = ZoneInfo("Asia/Tokyo")
HOUR_START = 9
HOUR_END = 23


class WeatherCalculator:
    """実質天気（9:00〜23:00 JST）を算出するドメインサービス"""

    def calculate(self, hourly_data: list[dict], jma_pops: list[dict]) -> Weather:
        """気温データ(OWM)と降水確率データ(JMA)から実質天気を算出する

        Args:
            hourly_data: OpenWeatherMap APIのhourly配列。各要素は dt, temp を持つ。
            jma_pops: 気象庁APIの降水確率。各要素は time(datetime), pop(int) を持つ。

        Returns:
            Weather: 実質天気情報

        Raises:
            ValueError: 対象時間帯のデータが存在しない場合
        """
        # 気温: 9:00〜23:00 JST のデータをフィルタ
        filtered_temps = []
        for entry in hourly_data:
            dt_utc = datetime.fromtimestamp(entry["dt"], tz=timezone.utc)
            dt_jst = dt_utc.astimezone(JST)
            if HOUR_START <= dt_jst.hour < HOUR_END:
                filtered_temps.append(entry["temp"])

        if not filtered_temps:
            raise ValueError("9:00〜23:00（JST）の気温データが存在しません")

        max_temp = round(max(filtered_temps), 1)
        min_temp = round(min(filtered_temps), 1)

        # 降水確率: JMA 6時間ブロックから9:00〜23:00に該当するものの最大値
        # 06:00→06-12時, 12:00→12-18時, 18:00→18-24時
        # 9:00〜23:00 に該当: 06:00, 12:00, 18:00 のブロック
        relevant_pops = []
        for pop_entry in jma_pops:
            pop_time = pop_entry["time"]
            if hasattr(pop_time, "hour"):
                hour = pop_time.hour
            else:
                hour = pop_time.astimezone(JST).hour
            # 06:00, 12:00, 18:00 のブロックが 9:00〜23:00 に該当
            if hour in (6, 12, 18):
                relevant_pops.append(pop_entry["pop"])

        if not relevant_pops:
            raise ValueError("9:00〜23:00（JST）の降水確率データが存在しません")

        pop = max(relevant_pops)

        return Weather(max_temp=max_temp, min_temp=min_temp, pop=pop)
