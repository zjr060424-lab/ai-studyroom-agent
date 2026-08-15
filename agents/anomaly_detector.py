from datetime import datetime, timedelta
from typing import Optional, Dict, List
from core.agent_base import BaseAgent
from core.message import Message, MessageType


class AnomalyDetectorAgent(BaseAgent):
    """
    Anomaly Detection Agent
    Identifies malicious occupancy, frequent cancellations, abnormal usage patterns,
    and automatically triggers restriction policies.
    """

    def __init__(self):
        super().__init__(
            agent_id="anomaly_agent",
            name="Anomaly Detection Agent",
            description="Detects abnormal behavior and enforces restriction policies",
        )
        self.user_activity_log: Dict[str, List[dict]] = {}
        self.anomaly_thresholds = {
            "max_daily_cancellations": 3,
            "max_consecutive_no_shows": 2,
            "min_session_duration_minutes": 15,
            "max_daily_reservations": 5,
            "suspicious_cancel_window_minutes": 5,
        }
        self.blacklist: set = set()
        self.anomaly_log: List[dict] = []

    def process(self, message: Message) -> Optional[Message]:
        # Anomaly detector monitors ALL messages passing through
        if message.msg_type in (MessageType.ANALYSIS_RESULT, MessageType.SCHEDULE_DECISION):
            return self._inspect_message(message)
        return None

    def tick(self) -> Optional[Message]:
        """Drain the whole queue each cycle.

        Unlike worker agents that handle one task per cycle, the observer
        may receive several mirrored messages per cycle and must not fall
        behind. Returns the most recent alert raised, if any.
        """
        alert = None
        while self.message_queue:
            msg = self.message_queue.pop(0)
            result = self.process(msg)
            if result:
                alert = result
        return alert

    def _inspect_message(self, message: Message) -> Optional[Message]:
        content = message.content
        analysis = content.get("analysis") or content
        user_id = analysis.get("user_id") or content.get("user_id")

        if not user_id:
            return None

        self._log_activity(user_id, message)

        # Check for anomalies
        anomalies = self._detect_anomalies(user_id)
        risk_score = self._calculate_risk_score(user_id)

        if anomalies:
            alerts = []
            for anomaly in anomalies:
                self.log(f"[ALERT] Anomaly detected: {anomaly['type']} for {user_id} | Score: {anomaly['severity']:.2f}")
                self.anomaly_log.append({"user_id": user_id, **anomaly})
                alerts.append(anomaly)

                # Auto-blacklist for severe violations
                if anomaly["severity"] > 0.8:
                    self.blacklist.add(user_id)

            return Message(
                msg_id=f"anomaly-{message.msg_id}",
                msg_type=MessageType.ANOMALY_ALERT,
                sender=self.agent_id,
                recipient="user",
                content={
                    "user_id": user_id,
                    "anomalies": alerts,
                    "risk_score": risk_score,
                    "is_blacklisted": user_id in self.blacklist,
                    "recommended_action": self._recommend_action(anomalies, risk_score),
                },
            )

        return None

    def _log_activity(self, user_id: str, message: Message):
        """Log user activity for pattern analysis."""
        if user_id not in self.user_activity_log:
            self.user_activity_log[user_id] = []

        self.user_activity_log[user_id].append({
            "timestamp": datetime.now(),
            "msg_type": message.msg_type.value,
            "action": message.content.get("action", "unknown"),
            "details": message.content,
        })

        # Keep only recent 100 entries
        if len(self.user_activity_log[user_id]) > 100:
            self.user_activity_log[user_id] = self.user_activity_log[user_id][-100:]

    def _detect_anomalies(self, user_id: str) -> List[dict]:
        """Detect various types of anomalies for a user."""
        anomalies = []
        activity = self.user_activity_log.get(user_id, [])

        if not activity:
            return anomalies

        # 1. Check for frequent cancellations
        recent_cancels = [a for a in activity
                         if a.get("action") == "cancel"
                         and (datetime.now() - a["timestamp"]).total_seconds() < 86400]
        if len(recent_cancels) > self.anomaly_thresholds["max_daily_cancellations"]:
            anomalies.append({
                "type": "frequent_cancellation",
                "severity": min(1.0, len(recent_cancels) / 10),
                "count": len(recent_cancels),
                "detail": f"{len(recent_cancels)} cancellations in the last 24h",
            })

        # 2. Check for suspicious short-lived reservations
        for a in activity:
            if (a.get("action") == "cancel" and
                a["details"].get("duration_minutes", 120) < 15):
                anomalies.append({
                    "type": "suspicious_short_reservation",
                    "severity": 0.6,
                    "detail": "Reservation canceled within suspiciously short window",
                })
                break

        # 3. Check for excessive daily reservations
        today_activity = [a for a in activity
                         if a["timestamp"].date() == datetime.now().date()]
        unique_sessions = len(set(
            str(a["details"].get("seat_id", a["details"].get("user_id")))
            for a in today_activity
        ))
        if unique_sessions > self.anomaly_thresholds["max_daily_reservations"]:
            anomalies.append({
                "type": "excessive_daily_reservations",
                "severity": min(1.0, unique_sessions / 10),
                "count": unique_sessions,
                "detail": f"{unique_sessions} reservation attempts today",
            })

        # 4. Simulate pattern-based detection (batch reservation detection)
        attempts_in_5min = sum(
            1 for a in activity[-10:]  # check last 10 activities
            if (datetime.now() - a["timestamp"]).total_seconds() < 300
        )
        if attempts_in_5min >= 5:
            anomalies.append({
                "type": "rapid_fire_reservations",
                "severity": 0.75,
                "count": attempts_in_5min,
                "detail": "Multiple reservation attempts in short time window",
            })

        return anomalies

    def _calculate_risk_score(self, user_id: str) -> float:
        """Calculate overall risk score for a user (0-1)."""
        activity = self.user_activity_log.get(user_id, [])
        if not activity:
            return 0.0

        score = 0.0
        anomalies = self._detect_anomalies(user_id)

        for anomaly in anomalies:
            score += anomaly["severity"] * 0.25

        # Blacklist penalty
        if user_id in self.blacklist:
            score += 0.5

        return min(1.0, score)

    def _recommend_action(self, anomalies: list, risk_score: float) -> str:
        """Recommend moderator action based on anomaly analysis."""
        max_severity = max((a["severity"] for a in anomalies), default=0)

        if max_severity > 0.8:
            return "immediate_ban"
        elif max_severity > 0.6:
            return "temporary_restriction"
        elif max_severity > 0.4:
            return "warning"
        return "monitor"

    def get_report(self) -> dict:
        """Generate anomaly detection report."""
        return {
            "total_anomalies": len(self.anomaly_log),
            "blacklisted_users": len(self.blacklist),
            "active_monitoring": len(self.user_activity_log),
            "recent_alerts": self.anomaly_log[-5:] if self.anomaly_log else [],
        }
