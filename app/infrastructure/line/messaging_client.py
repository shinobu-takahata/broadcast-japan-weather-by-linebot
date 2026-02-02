import requests

from infrastructure.exceptions import MessagingException
from utils.retry import retry


class LineMessagingClient:
    """LINE Messaging APIクライアント"""

    BASE_URL = "https://api.line.me/v2/bot/message"

    def __init__(self, channel_access_token: str) -> None:
        self.channel_access_token = channel_access_token

    @retry(max_attempts=3, backoff=[1, 2, 4])
    def reply_message(self, reply_token: str, text: str) -> None:
        """返信メッセージを送信

        Raises:
            MessagingException: メッセージ送信エラー
        """
        url = f"{self.BASE_URL}/reply"
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}",
            "Content-Type": "application/json",
        }
        data = {
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": text}],
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise MessagingException(f"LINE Reply Message送信エラー: {e}") from e

    @retry(max_attempts=3, backoff=[1, 2, 4])
    def push_message(self, user_id: str, message: str) -> None:
        """Push Messageを送信

        Raises:
            MessagingException: メッセージ送信エラー
        """
        url = f"{self.BASE_URL}/push"
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}",
            "Content-Type": "application/json",
        }
        data = {
            "to": user_id,
            "messages": [{"type": "text", "text": message}],
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise MessagingException(f"LINE Push Message送信エラー: {e}") from e
