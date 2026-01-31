from unittest.mock import MagicMock, patch

from domain.entities.user import User
from domain.value_objects.location import Location
from infrastructure.exceptions import GeocodingNotFoundException
from usecases.register_region import RegisterRegionUseCase


class TestRegisterRegionUseCase:
    def setup_method(self):
        self.mock_user_repo = MagicMock()
        self.mock_geocoding = MagicMock()
        self.mock_messaging = MagicMock()
        self.usecase = RegisterRegionUseCase(
            user_repository=self.mock_user_repo,
            geocoding_client=self.mock_geocoding,
            messaging_client=self.mock_messaging,
        )

    def test_new_user_registration(self):
        self.mock_geocoding.get_coordinates.return_value = (35.6619, 139.7041, "渋谷区")
        self.mock_user_repo.find_by_id.return_value = None

        self.usecase.execute("U1234", "渋谷区", "reply-token")

        self.mock_user_repo.save.assert_called_once()
        saved_user = self.mock_user_repo.save.call_args[0][0]
        assert saved_user.user_id == "U1234"
        assert saved_user.location.city_name == "渋谷区"
        self.mock_messaging.reply_message.assert_called_once_with(
            "reply-token", "渋谷区の天気をお届けします"
        )

    def test_existing_user_update(self):
        self.mock_geocoding.get_coordinates.return_value = (35.6938, 139.7034, "新宿区")
        existing_location = Location(city_name="渋谷区", latitude=35.6619, longitude=139.7041)
        existing_user = User(user_id="U1234", location=existing_location)
        self.mock_user_repo.find_by_id.return_value = existing_user

        self.usecase.execute("U1234", "新宿区", "reply-token")

        self.mock_user_repo.save.assert_called_once()
        saved_user = self.mock_user_repo.save.call_args[0][0]
        assert saved_user.location.city_name == "新宿区"
        self.mock_messaging.reply_message.assert_called_once_with(
            "reply-token", "新宿区の天気をお届けします"
        )

    def test_city_not_found(self):
        self.mock_geocoding.get_coordinates.side_effect = GeocodingNotFoundException(
            "地名が見つかりません"
        )

        self.usecase.execute("U1234", "あああ", "reply-token")

        self.mock_user_repo.save.assert_not_called()
        reply_text = self.mock_messaging.reply_message.call_args[0][1]
        assert "あああ" in reply_text
        assert "見つかりませんでした" in reply_text

    def test_unexpected_error(self):
        self.mock_geocoding.get_coordinates.side_effect = RuntimeError("unexpected")

        self.usecase.execute("U1234", "渋谷区", "reply-token")

        self.mock_user_repo.save.assert_not_called()
        reply_text = self.mock_messaging.reply_message.call_args[0][1]
        assert "エラーが発生しました" in reply_text
