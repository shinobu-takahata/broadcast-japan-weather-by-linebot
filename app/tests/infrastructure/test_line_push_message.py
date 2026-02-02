from unittest.mock import MagicMock, patch

import pytest

from infrastructure.exceptions import MessagingException
from infrastructure.line.messaging_client import LineMessagingClient


class TestLineMessagingClientPushMessage:
    def setup_method(self):
        self.client = LineMessagingClient(channel_access_token="test-token")

    @patch("infrastructure.line.messaging_client.requests.post")
    def test_push_message_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        self.client.push_message("U1234", "テストメッセージ")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["json"]["to"] == "U1234"
        assert call_kwargs.kwargs["json"]["messages"][0]["text"] == "テストメッセージ"
        assert "push" in call_kwargs.args[0]

    @patch("infrastructure.line.messaging_client.requests.post")
    def test_push_message_http_error(self, mock_post):
        import requests

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
        mock_post.return_value = mock_response

        with pytest.raises(MessagingException):
            self.client.push_message("U1234", "テスト")
