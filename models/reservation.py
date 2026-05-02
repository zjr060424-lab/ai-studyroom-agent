from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class ReservationStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


@dataclass
class Reservation:
    reservation_id: str
    user_id: str
    seat_id: str
    start_time: datetime
    end_time: datetime
    status: ReservationStatus = ReservationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    checked_in_at: Optional[datetime] = None
    no_show_risk: float = 0.0  # 0.0 - 1.0
    priority_score: float = 1.0
    notes: str = ""

    @property
    def duration_minutes(self) -> float:
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 60

    @property
    def is_active(self) -> bool:
        return self.status in (ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN)

    def cancel(self):
        if self.is_active:
            self.status = ReservationStatus.CANCELLED

    def mark_no_show(self):
        if self.status == ReservationStatus.CONFIRMED:
            self.status = ReservationStatus.NO_SHOW

    def complete(self):
        if self.status == ReservationStatus.CHECKED_IN:
            self.status = ReservationStatus.COMPLETED
