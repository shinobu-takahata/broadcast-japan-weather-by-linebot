from unittest.mock import MagicMock, patch

import pytest

from infrastructure.exceptions import JMAAPIException
from infrastructure.jma.area_mapper import JmaAreaMapper


SAMPLE_AREA_DATA = {
    "offices": {
        "140000": {"name": "神奈川県", "children": ["140010", "140020"]},
        "130000": {"name": "東京都", "children": ["130010", "130020"]},
    },
    "class10s": {
        "140010": {"name": "東部", "parent": "140000", "children": ["140011"]},
        "130010": {"name": "東京地方", "parent": "130000", "children": ["130011"]},
    },
    "class15s": {
        "140011": {"name": "横浜・川崎", "parent": "140010", "children": ["1410100"]},
        "130011": {"name": "東京", "parent": "130010", "children": ["1310100"]},
    },
    "class20s": {
        "1410100": {"name": "川崎市", "parent": "140011"},
        "1310100": {"name": "渋谷区", "parent": "130011"},
    },
}


class TestJmaAreaMapper:
    def setup_method(self):
        self.mapper = JmaAreaMapper()

    @patch("infrastructure.jma.area_mapper.requests.get")
    def test_find_codes_kawasaki(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SAMPLE_AREA_DATA
        mock_get.return_value = mock_response

        office_code, class10_code = self.mapper.find_codes("川崎市")

        assert office_code == "140000"
        assert class10_code == "140010"

    @patch("infrastructure.jma.area_mapper.requests.get")
    def test_find_codes_shibuya(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SAMPLE_AREA_DATA
        mock_get.return_value = mock_response

        office_code, class10_code = self.mapper.find_codes("渋谷区")

        assert office_code == "130000"
        assert class10_code == "130010"

    @patch("infrastructure.jma.area_mapper.requests.get")
    def test_find_codes_with_prefecture_prefix(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SAMPLE_AREA_DATA
        mock_get.return_value = mock_response

        office_code, class10_code = self.mapper.find_codes("神奈川県川崎市")

        assert office_code == "140000"
        assert class10_code == "140010"

    @patch("infrastructure.jma.area_mapper.requests.get")
    def test_find_codes_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SAMPLE_AREA_DATA
        mock_get.return_value = mock_response

        with pytest.raises(JMAAPIException, match="見つかりません"):
            self.mapper.find_codes("存在しない市")

    @patch("infrastructure.jma.area_mapper.requests.get")
    def test_area_data_cached(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SAMPLE_AREA_DATA
        mock_get.return_value = mock_response

        self.mapper.find_codes("川崎市")
        self.mapper.find_codes("渋谷区")

        # area.json は1回だけフェッチされる
        mock_get.assert_called_once()

    @patch("infrastructure.jma.area_mapper.requests.get")
    def test_fetch_error_raises(self, mock_get):
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("timeout")

        with pytest.raises(JMAAPIException):
            self.mapper.find_codes("川崎市")
