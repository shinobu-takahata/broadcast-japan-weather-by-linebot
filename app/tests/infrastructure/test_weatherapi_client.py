from unittest.mock import MagicMock, patch

import pytest

from infrastructure.exceptions import WeatherAPIException
from infrastructure.weatherapi.client import WeatherApiClient


class TestWeatherApiClient:
    def setup_method(self):
        self.client = WeatherApiClient(api_key="test-api-key")

    @patch("infrastructure.weatherapi.client.requests.get")
    def test_get_hourly_weather_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "forecast": {
                "forecastday": [
                    {
                        "hour": [
                            {"time": "2026-02-03 09:00", "temp_c": 8.5},
                            {"time": "2026-02-03 10:00", "temp_c": 9.0},
                        ]
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = self.client.get_hourly_weather(35.6619, 139.7041)

        assert len(result) == 2
        assert result[0]["time"] == "2026-02-03 09:00"
        assert result[0]["temp"] == 8.5
        assert result[1]["temp"] == 9.0
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["params"]["q"] == "35.6619,139.7041"
        assert call_kwargs.kwargs["params"]["key"] == "test-api-key"
        assert call_kwargs.kwargs["params"]["days"] == 1

    @patch("infrastructure.weatherapi.client.requests.get")
    def test_get_hourly_weather_empty_forecast(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"forecast": {"forecastday": []}}
        mock_get.return_value = mock_response

        result = self.client.get_hourly_weather(35.6619, 139.7041)
        assert result == []

    @patch("infrastructure.weatherapi.client.requests.get")
    def test_get_hourly_weather_no_forecast_key(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        result = self.client.get_hourly_weather(35.6619, 139.7041)
        assert result == []

    @patch("infrastructure.weatherapi.client.requests.get")
    def test_get_hourly_weather_http_error(self, mock_get):
        import requests

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401")
        mock_get.return_value = mock_response

        with pytest.raises(WeatherAPIException):
            self.client.get_hourly_weather(35.6619, 139.7041)

    @patch("infrastructure.weatherapi.client.requests.get")
    def test_get_hourly_weather_timeout(self, mock_get):
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("timeout")

        with pytest.raises(WeatherAPIException):
            self.client.get_hourly_weather(35.6619, 139.7041)
