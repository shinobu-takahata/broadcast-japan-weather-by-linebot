import base64
import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

from handlers.webhook import handler, verify_signature


class TestVerifySignature:
    def test_valid_signature(self):
        body = '{"events":[]}'
        secret = "test-secret"
        hash_value = hmac.new(
            secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256
        ).digest()
        signature = base64.b64encode(hash_value).decode("utf-8")

        assert verify_signature(body, signature, secret) is True

    def test_invalid_signature(self):
        assert verify_signature('{"events":[]}', "invalid", "test-secret") is False


class TestWebhookHandler:
    def _make_event(self, body: dict, secret: str = "test-secret") -> dict:
        body_str = json.dumps(body)
        hash_value = hmac.new(
            secret.encode("utf-8"), body_str.encode("utf-8"), hashlib.sha256
        ).digest()
        signature = base64.b64encode(hash_value).decode("utf-8")
        return {
            "body": body_str,
            "headers": {"x-line-signature": signature},
        }

    @patch("handlers.webhook._get_secret")
    @patch("handlers.webhook.RegisterRegionUseCase")
    @patch("handlers.webhook.LineMessagingClient")
    @patch("handlers.webhook.GsiGeocodingClient")
    @patch("handlers.webhook.DynamoDBUserRepository")
    @patch.dict(
        "os.environ",
        {
            "LINE_CHANNEL_SECRET_NAME": "secret-name",
            "LINE_CHANNEL_ACCESS_TOKEN_NAME": "token-name",
            "TABLE_NAME": "test-table",
        },
    )
    def test_message_event(self, mock_repo, mock_geo, mock_line, mock_usecase_cls, mock_secret):
        mock_secret.side_effect = lambda name: {
            "secret-name": "test-secret",
            "token-name": "test-token",
        }[name]

        body = {
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token",
                    "source": {"userId": "U1234"},
                    "message": {"type": "text", "text": "渋谷区"},
                }
            ]
        }
        event = self._make_event(body)

        result = handler(event, None)

        assert result["statusCode"] == 200
        mock_usecase_cls.return_value.execute.assert_called_once_with(
            "U1234", "渋谷区", "reply-token"
        )

    @patch("handlers.webhook._get_secret")
    @patch.dict(
        "os.environ",
        {
            "LINE_CHANNEL_SECRET_NAME": "secret-name",
            "LINE_CHANNEL_ACCESS_TOKEN_NAME": "token-name",
            "TABLE_NAME": "test-table",
        },
    )
    def test_invalid_signature_returns_401(self, mock_secret):
        mock_secret.return_value = "test-secret"
        event = {
            "body": '{"events":[]}',
            "headers": {"x-line-signature": "invalid-signature"},
        }

        result = handler(event, None)

        assert result["statusCode"] == 401
