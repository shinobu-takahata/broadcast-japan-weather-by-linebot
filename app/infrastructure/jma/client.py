from datetime import datetime

import requests

from infrastructure.exceptions import JMAAPIException
from utils.retry import retry

FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{office_code}.json"


class JmaForecastClient:
    """気象庁天気予報APIクライアント（降水確率取得用）"""

    @retry(max_attempts=3, backoff=[1, 2, 4])
    def get_pops(self, office_code: str, class10_code: str) -> list[dict]:
        """指定エリアの降水確率を取得

        Args:
            office_code: 気象庁オフィスコード（例: "140000"）
            class10_code: class10コード（例: "140010"）

        Returns:
            [{"time": datetime, "pop": int}, ...] 形式のリスト

        Raises:
            JMAAPIException: API呼び出しエラーまたはデータが見つからない場合
        """
        url = FORECAST_URL.format(office_code=office_code)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise JMAAPIException(f"気象庁予報API呼び出しエラー: {e}") from e

        data = response.json()
        return self._extract_pops(data, class10_code)

    def _extract_pops(self, data: list[dict], class10_code: str) -> list[dict]:
        """レスポンスから該当エリアの降水確率を抽出"""
        # timeSeries[1] が降水確率のデータ
        for forecast in data:
            time_series_list = forecast.get("timeSeries", [])
            if len(time_series_list) < 2:
                continue

            pop_series = time_series_list[1]
            time_defines = pop_series.get("timeDefines", [])
            areas = pop_series.get("areas", [])

            # 該当エリアを検索
            for area in areas:
                area_code = area.get("area", {}).get("code", "")
                if area_code == class10_code:
                    pops = area.get("pops", [])
                    result = []
                    for i, time_str in enumerate(time_defines):
                        if i < len(pops) and pops[i] != "":
                            dt = datetime.fromisoformat(time_str)
                            result.append({"time": dt, "pop": int(pops[i])})
                    return result

        raise JMAAPIException(
            f"気象庁予報データにclass10_code '{class10_code}' のデータが見つかりません"
        )
