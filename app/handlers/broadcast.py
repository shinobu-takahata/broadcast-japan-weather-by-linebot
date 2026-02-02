import os
from typing import Any

import boto3

from domain.services.weather_calculator import WeatherCalculator
from infrastructure.dynamodb.user_repository import DynamoDBUserRepository
from infrastructure.line.messaging_client import LineMessagingClient
from infrastructure.openweathermap.client import OpenWeatherMapClient
from usecases.broadcast_weather import BroadcastWeatherUseCase
from utils.logger import get_logger, log_error, log_info

logger = get_logger(__name__)


def _get_secret(secret_name: str) -> str:
    """Secrets Managerからシークレットを取得"""
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return response["SecretString"]


def handler(event: dict, context: Any) -> dict:
    """天気配信Lambda関数エントリポイント"""
    try:
        log_info(logger, "天気配信Lambda起動")

        table_name = os.environ["TABLE_NAME"]
        channel_access_token_name = os.environ["LINE_CHANNEL_ACCESS_TOKEN_NAME"]
        openweathermap_api_key_name = os.environ["OPENWEATHERMAP_API_KEY_NAME"]

        channel_access_token = _get_secret(channel_access_token_name)
        openweathermap_api_key = _get_secret(openweathermap_api_key_name)

        user_repository = DynamoDBUserRepository(table_name)
        weather_client = OpenWeatherMapClient(openweathermap_api_key)
        messaging_client = LineMessagingClient(channel_access_token)
        weather_calculator = WeatherCalculator()

        usecase = BroadcastWeatherUseCase(
            user_repository=user_repository,
            weather_client=weather_client,
            messaging_client=messaging_client,
            weather_calculator=weather_calculator,
        )
        usecase.execute()

        log_info(logger, "天気配信Lambda正常終了")
        return {"statusCode": 200, "body": "OK"}

    except Exception as e:
        log_error(logger, "天気配信Lambda異常終了", error=str(e))
        return {"statusCode": 500, "body": "Internal Server Error"}
