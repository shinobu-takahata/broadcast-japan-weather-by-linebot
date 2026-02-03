from unittest.mock import MagicMock, patch

from handlers.broadcast import handler


class TestBroadcastHandler:
    @patch("handlers.broadcast.BroadcastWeatherUseCase")
    @patch("handlers.broadcast.WeatherCalculator")
    @patch("handlers.broadcast.LineMessagingClient")
    @patch("handlers.broadcast.WeatherApiClient")
    @patch("handlers.broadcast.DynamoDBUserRepository")
    @patch("handlers.broadcast._get_secret")
    @patch.dict("os.environ", {
        "TABLE_NAME": "test-table",
        "LINE_CHANNEL_ACCESS_TOKEN_NAME": "test-token-name",
        "WEATHERAPI_API_KEY_NAME": "test-key-name",
    })
    def test_handler_success(
        self,
        mock_get_secret,
        mock_dynamo_repo,
        mock_weather_client,
        mock_line_client,
        mock_calculator,
        mock_usecase_class,
    ):
        mock_get_secret.side_effect = ["test-access-token", "test-api-key"]
        mock_usecase = MagicMock()
        mock_usecase_class.return_value = mock_usecase

        result = handler({}, None)

        assert result["statusCode"] == 200
        mock_usecase.execute.assert_called_once()

    @patch("handlers.broadcast.BroadcastWeatherUseCase")
    @patch("handlers.broadcast.WeatherCalculator")
    @patch("handlers.broadcast.LineMessagingClient")
    @patch("handlers.broadcast.WeatherApiClient")
    @patch("handlers.broadcast.DynamoDBUserRepository")
    @patch("handlers.broadcast._get_secret")
    @patch.dict("os.environ", {
        "TABLE_NAME": "test-table",
        "LINE_CHANNEL_ACCESS_TOKEN_NAME": "test-token-name",
        "WEATHERAPI_API_KEY_NAME": "test-key-name",
    })
    def test_handler_usecase_error(
        self,
        mock_get_secret,
        mock_dynamo_repo,
        mock_weather_client,
        mock_line_client,
        mock_calculator,
        mock_usecase_class,
    ):
        mock_get_secret.side_effect = ["test-access-token", "test-api-key"]
        mock_usecase = MagicMock()
        mock_usecase.execute.side_effect = RuntimeError("unexpected error")
        mock_usecase_class.return_value = mock_usecase

        result = handler({}, None)

        assert result["statusCode"] == 500
