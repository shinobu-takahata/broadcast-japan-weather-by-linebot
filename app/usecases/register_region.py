from domain.entities.user import User
from domain.repositories.user_repository import UserRepository
from domain.value_objects.location import Location
from infrastructure.exceptions import GeocodingAmbiguousException, GeocodingNotFoundException
from infrastructure.gsi.geocoding_client import GsiGeocodingClient
from infrastructure.line.messaging_client import LineMessagingClient
from utils.logger import get_logger, log_error, log_info

logger = get_logger(__name__)


class RegisterRegionUseCase:
    """地域設定ユースケース"""

    def __init__(
        self,
        user_repository: UserRepository,
        geocoding_client: GsiGeocodingClient,
        messaging_client: LineMessagingClient,
    ) -> None:
        self.user_repository = user_repository
        self.geocoding_client = geocoding_client
        self.messaging_client = messaging_client

    def execute(self, user_id: str, city_name: str, reply_token: str) -> None:
        """地域設定を実行"""
        log_info(logger, "地域設定開始", user_id=user_id, city_name=city_name)

        try:
            lat, lon, display_name = self.geocoding_client.get_coordinates(city_name)

            location = Location(
                city_name=display_name,
                latitude=lat,
                longitude=lon,
            )

            existing_user = self.user_repository.find_by_id(user_id)
            if existing_user:
                existing_user.update_location(location)
                self.user_repository.save(existing_user)
            else:
                user = User(user_id=user_id, location=location)
                self.user_repository.save(user)

            log_info(
                logger,
                "地域設定成功",
                user_id=user_id,
                city_name=display_name,
                lat=lat,
                lon=lon,
            )

            self.messaging_client.reply_message(
                reply_token, f"毎朝09:00に{display_name}の天気をお届けするよ U・x・U"
            )

        except GeocodingAmbiguousException as e:
            log_info(
                logger,
                "複数の候補",
                user_id=user_id,
                city_name=city_name,
                candidates=e.candidates,
            )
            candidate_list = "\n".join(
                f"{i + 1}. {name}" for i, name in enumerate(e.candidates)
            )
            self.messaging_client.reply_message(
                reply_token,
                f"複数の候補があります:\n{candidate_list}\n\n"
                "都道府県名を含めて再入力してください。",
            )

        except GeocodingNotFoundException:
            log_info(logger, "地名が見つからない", user_id=user_id, city_name=city_name)
            self.messaging_client.reply_message(
                reply_token,
                f"申し訳ございません。「{city_name}」が見つかりませんでした。\n\n"
                "正しい市区町村名を入力してください。\n"
                "例: 渋谷区、新宿区、横浜市",
            )

        except Exception as e:
            log_error(
                logger,
                "地域設定エラー",
                user_id=user_id,
                city_name=city_name,
                error=str(e),
            )
            try:
                self.messaging_client.reply_message(
                    reply_token,
                    "エラーが発生しました。しばらくしてからもう一度お試しください。",
                )
            except Exception:
                log_error(logger, "エラーメッセージ返信失敗", user_id=user_id)
