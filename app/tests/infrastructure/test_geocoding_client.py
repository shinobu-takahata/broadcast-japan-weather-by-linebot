from unittest.mock import MagicMock, patch

import pytest

from infrastructure.exceptions import GeocodingAPIException, GeocodingNotFoundException
from infrastructure.openweathermap.client import GeocodingClient


class TestGeocodingClient:
    def setup_method(self):
        self.client = GeocodingClient(api_key="test-api-key")

    @patch("infrastructure.openweathermap.client.requests.get")
    def test_get_coordinates_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "name": "Shibuya",
                "local_names": {"ja": "渋谷区"},
                "lat": 35.6619,
                "lon": 139.7041,
                "country": "JP",
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        lat, lon, name = self.client.get_coordinates("渋谷区")

        assert lat == 35.6619
        assert lon == 139.7041
        assert name == "渋谷区"
        mock_get.assert_called_once()

    @patch("infrastructure.openweathermap.client.requests.get")
    def test_get_coordinates_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with pytest.raises(GeocodingNotFoundException):
            self.client.get_coordinates("あああ")

    @patch("infrastructure.openweathermap.client.requests.get")
    def test_get_coordinates_no_local_names(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "name": "Shibuya",
                "lat": 35.6619,
                "lon": 139.7041,
                "country": "JP",
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        lat, lon, name = self.client.get_coordinates("渋谷区")

        assert name == "渋谷区"

    @patch("infrastructure.openweathermap.client.requests.get")
    def test_get_coordinates_http_error(self, mock_get):
        import requests

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
        mock_get.return_value = mock_response

        with pytest.raises(GeocodingAPIException):
            self.client.get_coordinates("渋谷区")
