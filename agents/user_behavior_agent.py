import random
from datetime import datetime
from typing import Optional
from core.agent_base import BaseAgent
from core.message import Message, MessageType


class UserBehaviorAgent(BaseAgent):
    """
    User Behavior Analysis Agent
    Analyzes historical reservation data, models user behavior patterns,
    predicts no-show probability, and dynamically adjusts reservation priority.
    """

    def __init__(self):
        super().__init__(
            agent_id="behavior_agent",
            name="User Behavior Analysis Agent",
            description="Analyzes user behavior, predicts no-show risk, adjusts priority",
        )
        self.user_profiles = {}  # cached user behavior data

    def process(self, message: Message) -> Optional[Message]:
        if message.msg_type == MessageType.REQUEST:
            return self._handle_request(message)
        return None

    def _handle_request(self, message: Message) -> Message:
        raw = message.content.get("raw_request", "")
        parsed = self._parse_request(raw)

        user_id = parsed.get("user_id", "unknown")
        user_profile = self._get_or_create_profile(user_id)
        no_show_risk = self._predict_no_show_risk(user_profile)
        priority = self._calculate_priority(parsed, user_profile, no_show_risk)

        self.log(f"Parsed request: {parsed.get('intent')} | User: {user_id}")
        self.log(f"No-show risk prediction: {no_show_risk:.1%}")
        self.log(f"Assigned priority: {priority:.2f}")

        return Message(
            msg_id=f"behavior-{message.msg_id}",
            msg_type=MessageType.ANALYSIS_RESULT,
            sender=self.agent_id,
            recipient="scheduler_agent",
            content={
                "analysis": {
                    "user_id": user_id,
                    "parsed_request": parsed,
                    "no_show_risk": no_show_risk,
                    "priority_score": priority,
                    "user_reliability": user_profile.get("reliability_score", 0.5),
                    "recommended_action": self._recommend_action(no_show_risk, user_profile),
                }
            },
            context={
                "source": "user_behavior_analysis",
                "risk_level": "high" if no_show_risk > 0.4 else "medium" if no_show_risk > 0.2 else "low",
            },
        )

    def _parse_request(self, raw: str) -> dict:
        """Parse natural language request to extract intent and parameters."""
        raw_lower = raw.lower()
        intent = "reserve"
        if "取消" in raw or "cancel" in raw:
            intent = "cancel"
        elif "release" in raw or "释放" in raw or "离开" in raw:
            intent = "release"

        # Extract time information
        time_slot = "afternoon"
        if "明天" in raw or "tomorrow" in raw:
            time_slot = "tomorrow_afternoon"
        if "下午" in raw or "afternoon" in raw:
            time_slot = "afternoon"
        elif "上午" in raw or "morning" in raw:
            time_slot = "morning"
        elif "晚上" in raw or "evening" in raw:
            time_slot = "evening"

        return {
            "intent": intent,
            "user_id": self._extract_user_id(raw),
            "time_slot": time_slot,
            "duration_minutes": 120,
            "preferred_area": self._extract_area(raw),
            "raw_text": raw,
        }

    def _extract_user_id(self, raw: str) -> str:
        """Simulate user ID extraction from request."""
        return f"STU{random.randint(2024001, 2024100)}"

    def _extract_area(self, raw: str) -> str:
        """Extract preferred study area from request."""
        raw_lower = raw.lower()
        if "quiet" in raw_lower or "安静" in raw_lower:
            return "A"
        if "discuss" in raw_lower or "讨论" in raw_lower or "小组" in raw_lower:
            return "C"
        return random.choice(["A", "B"])

    def _get_or_create_profile(self, user_id: str) -> dict:
        """Get or create user behavior profile."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = self._generate_profile(user_id)
        return self.user_profiles[user_id]

    def _generate_profile(self, user_id: str) -> dict:
        """Generate a simulated user profile based on user ID hash."""
        seed = hash(user_id) & 0xFFFFFFFF

        random.seed(seed)
        total = random.randint(5, 50)
        completed = random.randint(int(total * 0.6), total - 1)
        cancelled = random.randint(0, max(1, total - completed - 2))
        no_shows = max(0, total - completed - cancelled - random.randint(0, 2))
        consecutive = random.randint(0, min(2, no_shows))

        random.seed()  # reset seed
        return {
            "user_id": user_id,
            "total_reservations": total,
            "completed_reservations": completed,
            "cancelled_reservations": cancelled,
            "no_show_count": no_shows,
            "consecutive_no_shows": consecutive,
            "recent_cancellations_7d": random.randint(0, 3),
            "reliability_score": 1.0 - (no_shows / max(total, 1)) * 0.8,
            "avg_study_duration": random.randint(60, 240),
            "preferred_time": random.choice(["morning", "afternoon", "evening"]),
        }

    def _predict_no_show_risk(self, profile: dict) -> float:
        """Predict no-show probability based on historical behavior."""
        base_risk = 0.1
        risk = base_risk

        no_show_rate = profile["no_show_count"] / max(profile["total_reservations"], 1)
        risk += no_show_rate * 0.4
        risk += profile["consecutive_no_shows"] * 0.1
        risk += profile["recent_cancellations_7d"] * 0.05

        # High reliability reduces risk
        risk -= (profile.get("reliability_score", 0.5) - 0.5) * 0.1

        return max(0.0, min(1.0, risk))

    def _calculate_priority(self, parsed: dict, profile: dict, no_show_risk: float) -> float:
        """Calculate dynamic priority score (0-1)."""
        base_priority = 0.5
        priority = base_priority

        # Reliable users get higher priority
        priority += (profile.get("reliability_score", 0.5) - 0.5) * 0.3
        # High no-show risk reduces priority
        priority -= no_show_risk * 0.3
        # Peak time penalty
        if parsed.get("time_slot") == "afternoon":
            priority -= 0.05
        # Frequent users get slight bonus
        if profile["total_reservations"] > 20:
            priority += 0.1

        return max(0.1, min(1.0, priority))

    def _recommend_action(self, no_show_risk: float, profile: dict) -> str:
        """Recommend action based on risk assessment."""
        if no_show_risk > 0.6:
            return "require_deposit"
        elif no_show_risk > 0.3:
            return "normal_with_monitoring"
        return "approve_directly"
