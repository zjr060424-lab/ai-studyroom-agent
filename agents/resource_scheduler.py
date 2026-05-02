import random
from datetime import datetime, timedelta
from typing import Optional, List
from core.agent_base import BaseAgent
from core.message import Message, MessageType
from models.seat import Seat, SeatStatus


class ResourceSchedulerAgent(BaseAgent):
    """
    Resource Scheduling Agent
    Performs dynamic seat allocation combining real-time seat status
    with predictive analytics to optimize overall resource utilization.
    Implements a simplified reinforcement-learning-like allocation strategy.
    """

    def __init__(self):
        super().__init__(
            agent_id="scheduler_agent",
            name="Resource Scheduling Agent",
            description="Dynamic seat allocation with utilization optimization",
        )
        self.seats: List[Seat] = self._initialize_seats()
        self.allocation_history: List[dict] = []
        self.utilization_cache: dict = {}

    def _initialize_seats(self, count: int = 30) -> List[Seat]:
        """Initialize study room seats with varied configurations."""
        seats = []
        areas = {"A": {"floor": 2, "quiet": True, "desc": "Quiet Study Area"},
                 "B": {"floor": 3, "quiet": False, "desc": "General Study Area"},
                 "C": {"floor": 1, "quiet": False, "desc": "Discussion Area"}}

        for i in range(count):
            area_key = random.choice(list(areas.keys()))
            area = areas[area_key]
            seats.append(Seat(
                seat_id=f"{area_key}-{i+1:02d}",
                area=area_key,
                floor=area["floor"],
                is_quiet_zone=area["quiet"],
                has_power=random.choice([True, True, True, False]),
                is_window_seat=random.choice([True, False, False]),
                tags=["window"] if random.random() > 0.7 else [],
            ))
        return seats

    def process(self, message: Message) -> Optional[Message]:
        if message.msg_type == MessageType.ANALYSIS_RESULT:
            return self._handle_analysis(message)
        elif message.msg_type == MessageType.REQUEST:
            analysis = message.content.get("analysis", {})
            if analysis:
                return self._handle_analysis(message)
        return None

    def _handle_analysis(self, message: Message) -> Message:
        analysis = message.content.get("analysis", {})
        user_id = analysis.get("user_id", "unknown")
        no_show_risk = analysis.get("no_show_risk", 0.0)
        priority = analysis.get("priority_score", 0.5)
        parsed = analysis.get("parsed_request", {})
        intent = parsed.get("intent", "reserve")
        duration = parsed.get("duration_minutes", 120)
        preferred_area = parsed.get("preferred_area")

        self.log(f"Processing allocation for {user_id} | Risk: {no_show_risk:.1%} | Priority: {priority:.2f}")

        if intent == "release":
            result = self._handle_release(user_id)
            return Message(
                msg_id=f"sched-rel-{message.msg_id}",
                msg_type=MessageType.SCHEDULE_DECISION,
                sender=self.agent_id,
                recipient="executor_agent",
                content={"action": "release", "user_id": user_id, "success": result},
            )

        if intent == "cancel":
            return Message(
                msg_id=f"sched-can-{message.msg_id}",
                msg_type=MessageType.SCHEDULE_DECISION,
                sender=self.agent_id,
                recipient="executor_agent",
                content={"action": "cancel", "user_id": user_id},
            )

        # Find best seat using multi-factor scoring
        best_seat, score = self._select_best_seat(no_show_risk, priority, preferred_area)

        if best_seat is None:
            self.log("No available seats!", "WARNING")
            return self._no_seat_response(message)

        until = datetime.now() + timedelta(minutes=duration)
        best_seat.occupy(user_id, until)

        self.log(f"Allocated seat: {best_seat.seat_id} (Area {best_seat.area}) | Score: {score:.2f}")

        decision = {
            "action": "reserve",
            "user_id": user_id,
            "seat_id": best_seat.seat_id,
            "area": best_seat.area,
            "floor": best_seat.floor,
            "duration_minutes": duration,
            "allocation_score": score,
            "utilization_estimate": self._estimate_utilization(best_seat),
            "is_window_seat": best_seat.is_window_seat,
            "has_power": best_seat.has_power,
            "is_quiet_zone": best_seat.is_quiet_zone,
        }

        self.allocation_history.append(decision)

        return Message(
            msg_id=f"sched-{message.msg_id}",
            msg_type=MessageType.SCHEDULE_DECISION,
            sender=self.agent_id,
            recipient="executor_agent",
            content=decision,
        )

    def _select_best_seat(self, no_show_risk: float, priority: float,
                          preferred_area: Optional[str] = None) -> tuple:
        """Multi-factor seat selection using dynamic scoring."""
        available = [s for s in self.seats if s.is_available()]

        if not available:
            return None, 0.0

        if preferred_area:
            preferred = [s for s in available if s.area == preferred_area]
            if preferred:
                available = preferred

        # Score each available seat
        scored = []
        for seat in available:
            score = self._score_seat(seat, no_show_risk, priority)
            scored.append((seat, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # High-risk users get lower-quality seats (simulated RL penalty)
        if no_show_risk > 0.4 and len(scored) > 2:
            return scored[-1][0], scored[-1][1]

        return scored[0][0], scored[0][1]

    def _score_seat(self, seat: Seat, no_show_risk: float, priority: float) -> float:
        """Score a seat based on multiple factors."""
        score = 0.5  # base

        # Amenities bonus
        if seat.has_power:
            score += 0.1
        if seat.is_window_seat:
            score += 0.05
        if seat.is_quiet_zone:
            score += 0.1

        # Load balancing: prefer areas with lower utilization
        area_util = self._get_area_utilization(seat.area)
        if area_util < 0.5:
            score += 0.15
        elif area_util > 0.8:
            score -= 0.1

        # Quality score
        score += (seat.quality_score - 0.5) * 0.1

        # Penalty for excessive daily usage
        if seat.daily_usage_count > 5:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _get_area_utilization(self, area: str) -> float:
        """Calculate current utilization rate for an area."""
        area_seats = [s for s in self.seats if s.area == area]
        if not area_seats:
            return 0.0
        occupied = sum(1 for s in area_seats if s.status != SeatStatus.AVAILABLE)
        return occupied / len(area_seats)

    def _estimate_utilization(self, seat: Seat) -> dict:
        """Estimate utilization metrics after this allocation."""
        total = len(self.seats)
        occupied = sum(1 for s in self.seats if s.status != SeatStatus.AVAILABLE)
        area_util = self._get_area_utilization(seat.area)

        return {
            "overall_utilization": f"{(occupied / total * 100):.1f}%",
            f"area_{seat.area}_utilization": f"{area_util * 100:.1f}%",
            "total_seats": total,
            "occupied_seats": occupied,
            "available_seats": total - occupied,
        }

    def _handle_release(self, user_id: str) -> bool:
        """Release a seat occupied by the given user."""
        for seat in self.seats:
            if seat.current_user_id == user_id:
                seat.release()
                self.log(f"Released seat {seat.seat_id} from user {user_id}")
                return True
        return False

    def _no_seat_response(self, message: Message) -> Message:
        return Message(
            msg_id=f"sched-fail-{message.msg_id}",
            msg_type=MessageType.FEEDBACK,
            sender=self.agent_id,
            recipient="user",
            content={
                "error": "no_available_seats",
                "suggestion": "Try visiting during off-peak hours (morning or evening).",
                "available_areas": self._available_areas_summary(),
            },
        )

    def _available_areas_summary(self) -> dict:
        """Show availability by area."""
        summary = {}
        for area in ["A", "B", "C"]:
            area_seats = [s for s in self.seats if s.area == area]
            available = sum(1 for s in area_seats if s.is_available())
            summary[area] = {"total": len(area_seats), "available": available}
        return summary

    def get_stats(self) -> dict:
        """Get current scheduler statistics."""
        total = len(self.seats)
        occupied = sum(1 for s in self.seats if s.status != SeatStatus.AVAILABLE)
        return {
            "total_seats": total,
            "occupied": occupied,
            "available": total - occupied,
            "utilization": occupied / total * 100,
            "total_allocations": len(self.allocation_history),
        }
