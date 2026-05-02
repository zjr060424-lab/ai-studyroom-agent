from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class UserBehavior:
    total_reservations: int = 0
    completed_reservations: int = 0
    cancelled_reservations: int = 0
    no_show_count: int = 0
    avg_duration_minutes: float = 0.0
    preferred_areas: List[str] = field(default_factory=lambda: ["A", "B"])
    recent_cancellations_7d: int = 0
    consecutive_no_shows: int = 0
    reliability_score: float = 1.0  # 0.0 - 1.0
    peak_hour_usage: int = 0  # number of peak hour reservations

    @property
    def no_show_rate(self) -> float:
        if self.total_reservations == 0:
            return 0.0
        return self.no_show_count / self.total_reservations


@dataclass
class User:
    user_id: str
    name: str
    role: str = "student"  # student, teacher, staff
    behavior: UserBehavior = field(default_factory=UserBehavior)
    is_blacklisted: bool = False
    priority_level: int = 3  # 1 (lowest) - 5 (highest)

    def __post_init__(self):
        if isinstance(self.behavior, dict):
            self.behavior = UserBehavior(**self.behavior)
