from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import boto3

from domain.entities.user import User
from domain.repositories.user_repository import UserRepository
from domain.value_objects.location import Location
from utils.retry import retry


class DynamoDBUserRepository(UserRepository):
    """DynamoDB実装のUserRepository"""

    def __init__(self, table_name: str) -> None:
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(table_name)

    @retry(max_attempts=3, backoff=[1, 2, 4])
    def save(self, user: User) -> None:
        """ユーザーを保存（上書き）"""
        item = {
            "userId": user.user_id,
            "lat": Decimal(str(user.location.latitude)),
            "lon": Decimal(str(user.location.longitude)),
            "cityName": user.location.city_name,
            "createdAt": user.created_at.isoformat(),
            "updatedAt": user.updated_at.isoformat(),
        }
        self.table.put_item(Item=item)

    def find_by_id(self, user_id: str) -> Optional[User]:
        """ユーザーIDでユーザーを取得"""
        response = self.table.get_item(Key={"userId": user_id})
        if "Item" not in response:
            return None
        return self._to_entity(response["Item"])

    @staticmethod
    def _to_entity(item: dict) -> User:
        """DynamoDB Item → Userエンティティ変換"""
        location = Location(
            city_name=item["cityName"],
            latitude=float(item["lat"]),
            longitude=float(item["lon"]),
        )
        return User(
            user_id=item["userId"],
            location=location,
            created_at=datetime.fromisoformat(item["createdAt"]).replace(
                tzinfo=timezone.utc
            ),
            updated_at=datetime.fromisoformat(item["updatedAt"]).replace(
                tzinfo=timezone.utc
            ),
        )
