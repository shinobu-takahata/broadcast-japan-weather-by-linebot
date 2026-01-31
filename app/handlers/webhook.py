import base64
import hashlib
import hmac
import json
from typing import Any

import boto3

from infrastructure.dynamodb.user_repository import DynamoDBUserRepository
from infrastructure.line.messaging_client import LineMessagingClient
from infrastructure.openweathermap.client import GeocodingClient
from usecases.register_region import RegisterRegionUseCase
from utils.logger import get_logger, log_error, log_info

logger = get_logger(__name__)

CONFIRM_COMMANDS = ("設定確認", "確認", "設定")


def verify_signature(body: str, signature: str, channel_secret: str) -> bool:
    """LINE Webhookの署名検証"""
    hash_value = hmac.new(
        channel_secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    expected_signature = base64.b64encode(hash_value).decode("utf-8")
    return hmac.compare_digest(signature, expected_signature)


def _get_secret(secret_name: str) -> str:
    """Secrets Managerからシークレットを取得"""
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return response["SecretString"]


def _handle_message_event(
    event: dict,
    register_region_usecase: RegisterRegionUseCase,
) -> None:
    """メッセージイベントを処理"""
    message = event.get("message", {})
    if message.get("type") != "text":
        return

    user_id = event["source"]["userId"]
    text = message["text"].strip()
    reply_token = event["replyToken"]

    if text in CONFIRM_COMMANDS:
        return

    log_info(logger, "メッセージ受信", user_id=user_id, text=text)
    register_region_usecase.execute(user_id, text, reply_token)


def handler(event: dict, context: Any) -> dict:
    """Lambda関数エントリポイント"""
    import os

    try:
        body = event.get("body", "")
        headers = event.get("headers", {})
        signature = headers.get("x-line-signature") or headers.get("X-Line-Signature", "")

        channel_secret_name = os.environ["LINE_CHANNEL_SECRET_NAME"]
        channel_access_token_name = os.environ["LINE_CHANNEL_ACCESS_TOKEN_NAME"]
        api_key_name = os.environ["OPENWEATHERMAP_API_KEY_NAME"]
        table_name = os.environ["TABLE_NAME"]

        channel_secret = _get_secret(channel_secret_name)

        if not verify_signature(body, signature, channel_secret):
            log_error(logger, "署名検証失敗")
            return {"statusCode": 401, "body": "Unauthorized"}

        channel_access_token = _get_secret(channel_access_token_name)
        api_key = _get_secret(api_key_name)

        user_repository = DynamoDBUserRepository(table_name)
        geocoding_client = GeocodingClient(api_key)
        messaging_client = LineMessagingClient(channel_access_token)
        register_region_usecase = RegisterRegionUseCase(
            user_repository, geocoding_client, messaging_client
        )

        body_json = json.loads(body)
        events = body_json.get("events", [])

        for evt in events:
            if evt.get("type") == "message":
                _handle_message_event(evt, register_region_usecase)

        return {"statusCode": 200, "body": "OK"}

    except Exception as e:
        log_error(logger, "Webhook処理エラー", error=str(e))
        return {"statusCode": 500, "body": "Internal Server Error"}
