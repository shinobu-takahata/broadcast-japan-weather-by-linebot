from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.user import User


class UserRepository(ABC):
    """ユーザーリポジトリのインターフェース"""

    @abstractmethod
    def save(self, user: User) -> None:
        """ユーザーを保存"""

    @abstractmethod
    def find_by_id(self, user_id: str) -> Optional[User]:
        """ユーザーIDでユーザーを取得"""

    @abstractmethod
    def get_all_users(self) -> list[User]:
        """全ユーザーを取得"""
