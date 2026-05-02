from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class SeatStatus(Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"


@dataclass
class Seat:
    seat_id: str
    area: str  # A, B, C study areas
    floor: int = 1
    has_power: bool = True
    is_quiet_zone: bool = False
    is_window_seat: bool = False
    status: SeatStatus = SeatStatus.AVAILABLE
    current_user_id: Optional[str] = None
    reservation_until: Optional[datetime] = None
    daily_usage_count: int = 0
    quality_score: float = 1.0  # 0.0 - 1.0
    tags: list = field(default_factory=list)

    def is_available(self) -> bool:
        return self.status == SeatStatus.AVAILABLE

    def occupy(self, user_id: str, until: datetime) -> bool:
        if not self.is_available():
            return False
        self.status = SeatStatus.OCCUPIED
        self.current_user_id = user_id
        self.reservation_until = until
        self.daily_usage_count += 1
        return True

    def release(self) -> bool:
        if self.status == SeatStatus.AVAILABLE:
            return False
        self.status = SeatStatus.AVAILABLE
        self.current_user_id = None
        self.reservation_until = None
        return True
