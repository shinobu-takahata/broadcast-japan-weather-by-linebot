from unittest.mock import MagicMock, patch

import pytest

from infrastructure.exceptions import (
    GeocodingAmbiguousException,
    GeocodingAPIException,
    GeocodingNotFoundException,
)
from infrastructure.gsi.geocoding_client import GsiGeocodingClient


class TestGsiGeocodingClient:
    def setup_method(self):
        self.client = GsiGeocodingClient()

    @patch("infrastructure.gsi.geocoding_client.requests.get")
    def test_get_coordinates_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "geometry": {"coordinates": [139.7041, 35.6619]},
                "properties": {"title": "東京都渋谷区"},
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        lat, lon, name = self.client.get_coordinates("渋谷区")

        assert lat == 35.6619
        assert lon == 139.7041
        assert name == "東京都渋谷区"
        mock_get.assert_called_once()

    @patch("infrastructure.gsi.geocoding_client.requests.get")
    def test_get_coordinates_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with pytest.raises(GeocodingNotFoundException):
            self.client.get_coordinates("あああ")

    @patch("infrastructure.gsi.geocoding_client.requests.get")
    def test_get_coordinates_no_city_match(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "geometry": {"coordinates": [139.7041, 35.6619]},
                "properties": {"title": "渋谷駅"},
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with pytest.raises(GeocodingNotFoundException):
            self.client.get_coordinates("渋谷駅")

    @patch("infrastructure.gsi.geocoding_client.requests.get")
    def test_get_coordinates_ambiguous(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "geometry": {"coordinates": [139.4804, 35.6762]},
                "properties": {"title": "東京都府中市"},
            },
            {
                "geometry": {"coordinates": [133.2361, 34.5679]},
                "properties": {"title": "広島県府中市"},
            },
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with pytest.raises(GeocodingAmbiguousException) as exc_info:
            self.client.get_coordinates("府中市")

        assert "東京都府中市" in exc_info.value.candidates
        assert "広島県府中市" in exc_info.value.candidates

    @patch("infrastructure.gsi.geocoding_client.requests.get")
    def test_get_coordinates_duplicate_titles_resolved(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "geometry": {"coordinates": [139.7172, 35.6895]},
                "properties": {"title": "神奈川県川崎市"},
            },
            {
                "geometry": {"coordinates": [139.7173, 35.6896]},
                "properties": {"title": "神奈川県川崎市"},
            },
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        lat, lon, name = self.client.get_coordinates("神奈川県川崎市")

        assert name == "神奈川県川崎市"

    @patch("infrastructure.gsi.geocoding_client.requests.get")
    def test_get_coordinates_filters_non_city_suffix(self, mock_get):
        """末尾が市区町村でない候補が除外され、1件に絞られるケース"""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "geometry": {"coordinates": [139.7041, 35.6619]},
                "properties": {"title": "神奈川県川崎市"},
            },
            {
                "geometry": {"coordinates": [139.7050, 35.6630]},
                "properties": {"title": "神奈川県川崎郡"},
            },
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        lat, lon, name = self.client.get_coordinates("川崎")

        assert name == "神奈川県川崎市"

    @patch("infrastructure.gsi.geocoding_client.requests.get")
    def test_get_coordinates_http_error(self, mock_get):
        import requests

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
        mock_get.return_value = mock_response

        with pytest.raises(GeocodingAPIException):
            self.client.get_coordinates("渋谷区")

    @patch("infrastructure.gsi.geocoding_client.requests.get")
    def test_get_coordinates_request_exception(self, mock_get):
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("timeout")

        with pytest.raises(GeocodingAPIException):
            self.client.get_coordinates("渋谷区")
