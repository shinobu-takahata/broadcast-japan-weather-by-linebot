from datetime import datetime, timezone

from domain.entities.user import User
from domain.value_objects.location import Location


class TestUser:
    def test_create_new_user(self):
        location = Location(city_name="渋谷区", latitude=35.6619, longitude=139.7041)
        user = User(user_id="U1234", location=location)

        assert user.user_id == "U1234"
        assert user.location == location
        assert user.created_at.tzinfo == timezone.utc
        assert user.updated_at.tzinfo == timezone.utc
        assert user.created_at == user.updated_at

    def test_create_with_explicit_timestamps(self):
        location = Location(city_name="渋谷区", latitude=35.6619, longitude=139.7041)
        ts = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        user = User(user_id="U1234", location=location, created_at=ts, updated_at=ts)

        assert user.created_at == ts
        assert user.updated_at == ts

    def test_update_location(self):
        location1 = Location(city_name="渋谷区", latitude=35.6619, longitude=139.7041)
        user = User(user_id="U1234", location=location1)
        original_created_at = user.created_at
        original_updated_at = user.updated_at

        location2 = Location(city_name="新宿区", latitude=35.6938, longitude=139.7034)
        user.update_location(location2)

        assert user.location == location2
        assert user.created_at == original_created_at
        assert user.updated_at >= original_updated_at
