from unittest.mock import MagicMock, patch

import pytest

from infrastructure.exceptions import WeatherAPIException
from infrastructure.openweathermap.client import OpenWeatherMapClient


class TestOpenWeatherMapClient:
    def setup_method(self):
        self.client = OpenWeatherMapClient(api_key="test-api-key")

    @patch("infrastructure.openweathermap.client.requests.get")
    def test_get_hourly_weather_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "hourly": [
                {"dt": 1706497200, "temp": 8.5, "pop": 0.2},
                {"dt": 1706500800, "temp": 9.0, "pop": 0.3},
            ]
        }
        mock_get.return_value = mock_response

        result = self.client.get_hourly_weather(35.6619, 139.7041)

        assert len(result) == 2
        assert result[0]["temp"] == 8.5
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["params"]["lat"] == 35.6619
        assert call_kwargs.kwargs["params"]["lon"] == 139.7041
        assert call_kwargs.kwargs["params"]["appid"] == "test-api-key"

    @patch("infrastructure.openweathermap.client.requests.get")
    def test_get_hourly_weather_empty_hourly(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        result = self.client.get_hourly_weather(35.6619, 139.7041)
        assert result == []

    @patch("infrastructure.openweathermap.client.requests.get")
    def test_get_hourly_weather_http_error(self, mock_get):
        import requests

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401")
        mock_get.return_value = mock_response

        with pytest.raises(WeatherAPIException):
            self.client.get_hourly_weather(35.6619, 139.7041)

    @patch("infrastructure.openweathermap.client.requests.get")
    def test_get_hourly_weather_timeout(self, mock_get):
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("timeout")

        with pytest.raises(WeatherAPIException):
            self.client.get_hourly_weather(35.6619, 139.7041)
