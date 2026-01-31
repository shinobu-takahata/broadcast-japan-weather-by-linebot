from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from domain.value_objects.location import Location


@dataclass
class User:
    """ユーザーエンティティ"""

    user_id: str
    location: Location
    created_at: Optional[datetime] = field(default=None)
    updated_at: Optional[datetime] = field(default=None)

    def __post_init__(self) -> None:
        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def update_location(self, location: Location) -> None:
        """地域を更新"""
        self.location = location
        self.updated_at = datetime.now(timezone.utc)
