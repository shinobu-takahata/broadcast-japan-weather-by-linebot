class GeocodingNotFoundException(Exception):
    """地名が見つからない場合の例外"""


class GeocodingAmbiguousException(Exception):
    """複数の候補が見つかった場合の例外"""

    def __init__(self, message: str, candidates: list[str]) -> None:
        super().__init__(message)
        self.candidates = candidates


class GeocodingAPIException(Exception):
    """Geocoding APIのエラー"""


class MessagingException(Exception):
    """LINE Messaging APIのエラー"""


class RepositoryException(Exception):
    """データベース操作のエラー"""
