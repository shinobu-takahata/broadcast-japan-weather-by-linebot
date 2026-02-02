import requests

from infrastructure.exceptions import JMAAPIException
from utils.retry import retry

AREA_JSON_URL = "https://www.jma.go.jp/bosai/common/const/area.json"


class JmaAreaMapper:
    """市区町村名から気象庁のoffice_codeとclass10_codeを取得するマッパー"""

    def __init__(self) -> None:
        self._area_data: dict | None = None

    @retry(max_attempts=3, backoff=[1, 2, 4])
    def _fetch_area_data(self) -> dict:
        try:
            response = requests.get(AREA_JSON_URL, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise JMAAPIException(f"気象庁area.json取得エラー: {e}") from e
        return response.json()

    def _get_area_data(self) -> dict:
        if self._area_data is None:
            self._area_data = self._fetch_area_data()
        return self._area_data

    def find_codes(self, city_name: str) -> tuple[str, str]:
        """市区町村名からoffice_codeとclass10_codeを返す

        Args:
            city_name: 市区町村名（例: "川崎市", "渋谷区"）

        Returns:
            (office_code, class10_code) のタプル

        Raises:
            JMAAPIException: 該当する地域が見つからない場合
        """
        area_data = self._get_area_data()
        class20s = area_data.get("class20s", {})
        class15s = area_data.get("class15s", {})
        class10s = area_data.get("class10s", {})
        offices = area_data.get("offices", {})

        # class20s から city_name に一致するエントリを検索
        # 「神奈川県川崎市」のように県名付きの場合、末尾の市区町村名でもマッチさせる
        target_parent = None
        for code, info in class20s.items():
            name = info.get("name", "")
            if name == city_name or city_name.endswith(name):
                target_parent = info.get("parent")
                break

        if target_parent is None:
            raise JMAAPIException(f"気象庁エリア情報に '{city_name}' が見つかりません")

        # class15s → class10s → offices を辿る
        current_code = target_parent

        # class15s にある場合、その parent を取得
        if current_code in class15s:
            current_code = class15s[current_code].get("parent", current_code)

        # class10s にある場合、class10_code として記録し、parent で office を取得
        if current_code in class10s:
            class10_code = current_code
            office_code = class10s[current_code].get("parent", "")
            if office_code in offices:
                return (office_code, class10_code)

        raise JMAAPIException(
            f"'{city_name}' のoffice_code/class10_codeを特定できません"
        )
