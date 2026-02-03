from collections import defaultdict

from domain.repositories.user_repository import UserRepository
from domain.services.weather_calculator import WeatherCalculator
from infrastructure.exceptions import JMAAPIException, MessagingException, WeatherAPIException
from infrastructure.jma.area_mapper import JmaAreaMapper
from infrastructure.jma.client import JmaForecastClient
from infrastructure.line.messaging_client import LineMessagingClient
from infrastructure.weatherapi.client import WeatherApiClient
from utils.logger import get_logger, log_error, log_info

logger = get_logger(__name__)

MESSAGE_TEMPLATE = """おはよう U・x・U
{city_name}のお出かけ時のお天気をお知らせするよ☀️☔️☁️⛄️

最高気温: {max_temp}℃
最低気温: {min_temp}℃
降水確率: {pop}%"""


class BroadcastWeatherUseCase:
    """天気配信ユースケース"""

    def __init__(
        self,
        user_repository: UserRepository,
        weather_client: WeatherApiClient,
        messaging_client: LineMessagingClient,
        weather_calculator: WeatherCalculator,
        jma_client: JmaForecastClient,
        jma_area_mapper: JmaAreaMapper,
    ) -> None:
        self.user_repository = user_repository
        self.weather_client = weather_client
        self.messaging_client = messaging_client
        self.weather_calculator = weather_calculator
        self.jma_client = jma_client
        self.jma_area_mapper = jma_area_mapper

    def execute(self) -> None:
        """全ユーザーに天気情報を配信"""
        log_info(logger, "天気配信処理を開始")

        users = self.user_repository.get_all_users()
        if not users:
            log_info(logger, "配信対象ユーザーなし")
            return

        # 緯度経度でグルーピング
        groups: dict[tuple[float, float], list] = defaultdict(list)
        for user in users:
            key = (user.location.latitude, user.location.longitude)
            groups[key].append(user)

        log_info(
            logger,
            "ユーザー取得完了",
            total_users=len(users),
            unique_locations=len(groups),
        )

        success_count = 0
        failure_count = 0

        for (lat, lon), group_users in groups.items():
            city_name = group_users[0].location.city_name

            # 天気情報取得（気温: OWM）
            try:
                hourly_data = self.weather_client.get_hourly_weather(lat, lon)
            except WeatherAPIException as e:
                log_error(
                    logger,
                    "天気情報取得失敗",
                    error=str(e),
                    lat=lat,
                    lon=lon,
                    city_name=city_name,
                    skipped_users=len(group_users),
                )
                failure_count += len(group_users)
                continue

            # 降水確率取得（JMA）
            try:
                office_code, class10_code = self.jma_area_mapper.find_codes(city_name)
                jma_pops = self.jma_client.get_pops(office_code, class10_code)
            except JMAAPIException as e:
                log_error(
                    logger,
                    "気象庁API取得失敗",
                    error=str(e),
                    city_name=city_name,
                    skipped_users=len(group_users),
                )
                failure_count += len(group_users)
                continue

            # 実質天気算出
            try:
                weather = self.weather_calculator.calculate(hourly_data, jma_pops)
            except ValueError as e:
                log_error(
                    logger,
                    "実質天気算出失敗",
                    error=str(e),
                    lat=lat,
                    lon=lon,
                    city_name=city_name,
                    skipped_users=len(group_users),
                )
                failure_count += len(group_users)
                continue

            # メッセージ配信
            message = MESSAGE_TEMPLATE.format(
                city_name=city_name,
                max_temp=weather.max_temp,
                min_temp=weather.min_temp,
                pop=weather.pop,
            )

            for user in group_users:
                try:
                    self.messaging_client.push_message(user.user_id, message)
                    success_count += 1
                except MessagingException as e:
                    log_error(
                        logger,
                        "メッセージ配信失敗",
                        error=str(e),
                        user_id=user.user_id,
                    )
                    failure_count += 1

        log_info(
            logger,
            "天気配信処理を完了",
            success_count=success_count,
            failure_count=failure_count,
        )
