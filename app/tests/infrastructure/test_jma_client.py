from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from infrastructure.exceptions import JMAAPIException
from infrastructure.jma.client import JmaForecastClient

JST = ZoneInfo("Asia/Tokyo")

SAMPLE_FORECAST_RESPONSE = [
    {
        "timeSeries": [
            {
                "timeDefines": ["2026-02-03T17:00:00+09:00"],
                "areas": [{"area": {"code": "140010"}, "weatherCodes": ["100"]}],
            },
            {
                "timeDefines": [
                    "2026-02-03T00:00:00+09:00",
                    "2026-02-03T06:00:00+09:00",
                    "2026-02-03T12:00:00+09:00",
                    "2026-02-03T18:00:00+09:00",
                ],
                "areas": [
                    {
                        "area": {"code": "140010"},
                        "pops": ["10", "20", "30", "40"],
                    },
                    {
                        "area": {"code": "140020"},
                        "pops": ["50", "60", "70", "80"],
                    },
                ],
            },
        ],
    },
]


class TestJmaForecastClient:
    def setup_method(self):
        self.client = JmaForecastClient()

    @patch("infrastructure.jma.client.requests.get")
    def test_get_pops_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SAMPLE_FORECAST_RESPONSE
        mock_get.return_value = mock_response

        result = self.client.get_pops("140000", "140010")

        assert len(result) == 4
        assert result[0]["pop"] == 10
        assert result[0]["time"] == datetime(2026, 2, 3, 0, 0, 0, tzinfo=JST)
        assert result[1]["pop"] == 20
        assert result[2]["pop"] == 30
        assert result[3]["pop"] == 40

    @patch("infrastructure.jma.client.requests.get")
    def test_get_pops_different_area(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SAMPLE_FORECAST_RESPONSE
        mock_get.return_value = mock_response

        result = self.client.get_pops("140000", "140020")

        assert len(result) == 4
        assert result[0]["pop"] == 50

    @patch("infrastructure.jma.client.requests.get")
    def test_get_pops_area_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = SAMPLE_FORECAST_RESPONSE
        mock_get.return_value = mock_response

        with pytest.raises(JMAAPIException, match="見つかりません"):
            self.client.get_pops("140000", "999999")

    @patch("infrastructure.jma.client.requests.get")
    def test_get_pops_http_error(self, mock_get):
        import requests

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        mock_get.return_value = mock_response

        with pytest.raises(JMAAPIException):
            self.client.get_pops("140000", "140010")

    @patch("infrastructure.jma.client.requests.get")
    def test_get_pops_timeout(self, mock_get):
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("timeout")

        with pytest.raises(JMAAPIException):
            self.client.get_pops("140000", "140010")

    @patch("infrastructure.jma.client.requests.get")
    def test_get_pops_empty_pop_string_skipped(self, mock_get):
        response = [
            {
                "timeSeries": [
                    {"timeDefines": [], "areas": []},
                    {
                        "timeDefines": [
                            "2026-02-03T00:00:00+09:00",
                            "2026-02-03T06:00:00+09:00",
                        ],
                        "areas": [
                            {
                                "area": {"code": "140010"},
                                "pops": ["", "20"],
                            },
                        ],
                    },
                ],
            },
        ]
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = response
        mock_get.return_value = mock_response

        result = self.client.get_pops("140000", "140010")

        assert len(result) == 1
        assert result[0]["pop"] == 20
