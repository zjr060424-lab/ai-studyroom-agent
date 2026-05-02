"""Utility helpers for the AI Study Room Scheduling Agent."""


from datetime import datetime, timedelta


def format_timestamp(dt: datetime = None) -> str:
    """Format a timestamp for logging."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def generate_reservation_id() -> str:
    """Generate a unique reservation ID."""
    import random
    ts = datetime.now().strftime("%Y%m%d")
    seq = random.randint(10000, 99999)
    return f"RSV-{ts}-{seq}"


def generate_user_id(role: str = "STU") -> str:
    """Generate a sample user ID."""
    import random
    return f"{role}{random.randint(2024001, 2024999)}"


def calculate_utilization(occupied: int, total: int) -> float:
    """Calculate resource utilization percentage."""
    if total == 0:
        return 0.0
    return (occupied / total) * 100


def time_slot_to_hours(slot: str) -> tuple:
    """Convert a time slot name to (start_hour, end_hour)."""
    mapping = {
        "morning": (8, 12),
        "afternoon": (13, 17),
        "evening": (18, 22),
        "full_day": (8, 22),
    }
    return mapping.get(slot, (8, 22))


def format_duration(minutes: int) -> str:
    """Format minutes into a human-readable string."""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h{mins:02d}" if mins > 0 else f"{hours}h"
    return f"{mins}min"
