from unittest.mock import MagicMock

from domain.entities.user import User
from domain.value_objects.location import Location
from domain.value_objects.weather import Weather
from infrastructure.exceptions import MessagingException, WeatherAPIException
from usecases.broadcast_weather import BroadcastWeatherUseCase


def _make_user(user_id: str, city_name: str, lat: float, lon: float) -> User:
    location = Location(city_name=city_name, latitude=lat, longitude=lon)
    return User(user_id=user_id, location=location)


class TestBroadcastWeatherUseCase:
    def setup_method(self):
        self.mock_user_repo = MagicMock()
        self.mock_weather_client = MagicMock()
        self.mock_messaging = MagicMock()
        self.mock_calculator = MagicMock()
        self.usecase = BroadcastWeatherUseCase(
            user_repository=self.mock_user_repo,
            weather_client=self.mock_weather_client,
            messaging_client=self.mock_messaging,
            weather_calculator=self.mock_calculator,
        )

    def test_broadcast_single_user(self):
        user = _make_user("U1234", "渋谷区", 35.6619, 139.7041)
        self.mock_user_repo.get_all_users.return_value = [user]
        self.mock_weather_client.get_hourly_weather.return_value = [{"dt": 0, "temp": 20.0, "pop": 0.5}]
        self.mock_calculator.calculate.return_value = Weather(max_temp=25.0, min_temp=18.0, pop=50)

        self.usecase.execute()

        self.mock_weather_client.get_hourly_weather.assert_called_once_with(35.6619, 139.7041)
        self.mock_calculator.calculate.assert_called_once()
        self.mock_messaging.push_message.assert_called_once()
        message = self.mock_messaging.push_message.call_args[0][1]
        assert "渋谷区" in message
        assert "25.0" in message
        assert "18.0" in message
        assert "50" in message

    def test_broadcast_grouped_users(self):
        user1 = _make_user("U1", "渋谷区", 35.6619, 139.7041)
        user2 = _make_user("U2", "渋谷区", 35.6619, 139.7041)
        user3 = _make_user("U3", "新宿区", 35.6938, 139.7034)
        self.mock_user_repo.get_all_users.return_value = [user1, user2, user3]
        self.mock_weather_client.get_hourly_weather.return_value = [{"dt": 0, "temp": 20.0, "pop": 0.5}]
        self.mock_calculator.calculate.return_value = Weather(max_temp=25.0, min_temp=18.0, pop=50)

        self.usecase.execute()

        # 2つのユニークな緯度経度 → API呼び出し2回
        assert self.mock_weather_client.get_hourly_weather.call_count == 2
        # 3ユーザー全員にメッセージ配信
        assert self.mock_messaging.push_message.call_count == 3

    def test_no_users(self):
        self.mock_user_repo.get_all_users.return_value = []

        self.usecase.execute()

        self.mock_weather_client.get_hourly_weather.assert_not_called()
        self.mock_messaging.push_message.assert_not_called()

    def test_weather_api_failure_skips_group(self):
        user1 = _make_user("U1", "渋谷区", 35.6619, 139.7041)
        user2 = _make_user("U2", "新宿区", 35.6938, 139.7034)
        self.mock_user_repo.get_all_users.return_value = [user1, user2]

        def side_effect(lat, lon):
            if lat == 35.6619:
                raise WeatherAPIException("API error")
            return [{"dt": 0, "temp": 20.0, "pop": 0.5}]

        self.mock_weather_client.get_hourly_weather.side_effect = side_effect
        self.mock_calculator.calculate.return_value = Weather(max_temp=25.0, min_temp=18.0, pop=50)

        self.usecase.execute()

        # 渋谷区はスキップ、新宿区のみ配信
        assert self.mock_messaging.push_message.call_count == 1
        assert self.mock_messaging.push_message.call_args[0][0] == "U2"

    def test_push_message_failure_skips_user(self):
        user1 = _make_user("U1", "渋谷区", 35.6619, 139.7041)
        user2 = _make_user("U2", "渋谷区", 35.6619, 139.7041)
        self.mock_user_repo.get_all_users.return_value = [user1, user2]
        self.mock_weather_client.get_hourly_weather.return_value = [{"dt": 0, "temp": 20.0, "pop": 0.5}]
        self.mock_calculator.calculate.return_value = Weather(max_temp=25.0, min_temp=18.0, pop=50)

        self.mock_messaging.push_message.side_effect = [
            MessagingException("送信失敗"),
            None,
        ]

        self.usecase.execute()

        # 両方呼ばれるが、1つ目は失敗
        assert self.mock_messaging.push_message.call_count == 2

    def test_calculator_failure_skips_group(self):
        user = _make_user("U1", "渋谷区", 35.6619, 139.7041)
        self.mock_user_repo.get_all_users.return_value = [user]
        self.mock_weather_client.get_hourly_weather.return_value = []
        self.mock_calculator.calculate.side_effect = ValueError("データなし")

        self.usecase.execute()

        self.mock_messaging.push_message.assert_not_called()
