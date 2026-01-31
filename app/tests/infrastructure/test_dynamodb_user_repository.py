from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

from domain.entities.user import User
from domain.value_objects.location import Location
from infrastructure.dynamodb.user_repository import DynamoDBUserRepository


class TestDynamoDBUserRepository:
    @patch("infrastructure.dynamodb.user_repository.boto3")
    def setup_method(self, method, mock_boto3):
        self.mock_table = MagicMock()
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_dynamodb
        self.repo = DynamoDBUserRepository(table_name="test-table")

    def test_save_user(self):
        location = Location(city_name="渋谷区", latitude=35.6619, longitude=139.7041)
        now = datetime(2026, 1, 31, 0, 0, 0, tzinfo=timezone.utc)
        user = User(user_id="U1234", location=location, created_at=now, updated_at=now)

        self.repo.save(user)

        self.mock_table.put_item.assert_called_once()
        item = self.mock_table.put_item.call_args.kwargs["Item"]
        assert item["userId"] == "U1234"
        assert item["lat"] == Decimal("35.6619")
        assert item["lon"] == Decimal("139.7041")
        assert item["cityName"] == "渋谷区"

    def test_find_by_id_found(self):
        self.mock_table.get_item.return_value = {
            "Item": {
                "userId": "U1234",
                "lat": Decimal("35.6619"),
                "lon": Decimal("139.7041"),
                "cityName": "渋谷区",
                "createdAt": "2026-01-31T00:00:00+00:00",
                "updatedAt": "2026-01-31T00:00:00+00:00",
            }
        }

        user = self.repo.find_by_id("U1234")

        assert user is not None
        assert user.user_id == "U1234"
        assert user.location.city_name == "渋谷区"
        assert user.location.latitude == 35.6619

    def test_find_by_id_not_found(self):
        self.mock_table.get_item.return_value = {}

        user = self.repo.find_by_id("U9999")

        assert user is None
