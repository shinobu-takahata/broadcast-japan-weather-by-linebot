class GeocodingNotFoundException(Exception):
    """地名が見つからない場合の例外"""


class GeocodingAPIException(Exception):
    """Geocoding APIのエラー"""


class MessagingException(Exception):
    """LINE Messaging APIのエラー"""


class RepositoryException(Exception):
    """データベース操作のエラー"""
