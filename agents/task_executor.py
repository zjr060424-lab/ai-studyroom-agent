import random
from datetime import datetime
from typing import Optional
from core.agent_base import BaseAgent
from core.message import Message, MessageType


class TaskExecutorAgent(BaseAgent):
    """
    Task Execution Agent (Tool-calling type)
    Executes reservation, release, notification operations through API calls,
    completing the action-feedback loop of the system.
    """

    def __init__(self):
        super().__init__(
            agent_id="executor_agent",
            name="Task Execution Agent",
            description="Executes API calls for reservations, releases, and notifications",
        )
        self.api_simulator = APISimulator()
        self.execution_log: list = []
        self.success_count = 0
        self.failure_count = 0

    def process(self, message: Message) -> Optional[Message]:
        if message.msg_type == MessageType.SCHEDULE_DECISION:
            return self._execute_decision(message)
        return None

    def _execute_decision(self, message: Message) -> Message:
        decision = message.content
        action = decision.get("action", "unknown")

        self.log(f"Executing action: {action}")

        if action == "reserve":
            return self._execute_reservation(decision, message)
        elif action == "release":
            return self._execute_release(decision, message)
        elif action == "cancel":
            return self._execute_cancellation(decision, message)
        else:
            return self._error_response(f"Unknown action: {action}", message)

    def _execute_reservation(self, decision: dict, message: Message) -> Message:
        user_id = decision["user_id"]
        seat_id = decision["seat_id"]

        # Step 1: Check availability via API
        self.log(f"[API] Checking availability: {seat_id} ...")
        available = self.api_simulator.check_availability(seat_id)

        if not available:
            self.failure_count += 1
            self.log(f"[API] Seat {seat_id} no longer available!", "WARNING")
            return Message(
                msg_id=f"exec-fail-{message.msg_id}",
                msg_type=MessageType.EXECUTION_RESULT,
                sender=self.agent_id,
                recipient="user",
                content={"status": "failed", "reason": "seat_no_longer_available",
                         "suggestion": "Try a different area or time slot"},
            )

        # Step 2: Create reservation via API
        self.log(f"[API] Creating reservation: {user_id} -> {seat_id} ...")
        reservation = self.api_simulator.create_reservation(user_id, seat_id, decision)

        if reservation["success"]:
            self.success_count += 1
            self.execution_log.append(reservation)

            self.log(f"[API] [OK] Reservation confirmed: {reservation['reservation_id']}")

            # Step 3: Send notification (simulated)
            self._send_notification(user_id, seat_id, "confirmed")

            return Message(
                msg_id=f"exec-{message.msg_id}",
                msg_type=MessageType.EXECUTION_RESULT,
                sender=self.agent_id,
                recipient="user",
                content={
                    "status": "success",
                    "action": "reserve",
                    "reservation": reservation,
                    "user_id": user_id,
                    "seat_id": seat_id,
                    "execution_time_ms": random.randint(120, 450),
                },
            )
        else:
            self.failure_count += 1
            self.log(f"[API] Reservation failed for {seat_id}", "ERROR")
            return self._error_response("API reservation failed", message)

    def _execute_release(self, decision: dict, message: Message) -> Message:
        user_id = decision.get("user_id", "unknown")
        self.log(f"[API] Releasing seat for user: {user_id} ...")

        result = self.api_simulator.release_seat(user_id)
        if result["success"]:
            self.log(f"[API] Seat released successfully")
            self._send_notification(user_id, None, "released")

            return Message(
                msg_id=f"exec-rel-{message.msg_id}",
                msg_type=MessageType.EXECUTION_RESULT,
                sender=self.agent_id,
                recipient="user",
                content={"status": "success", "action": "release", "detail": result},
            )

        return self._error_response("Release failed - no active reservation found", message)

    def _execute_cancellation(self, decision: dict, message: Message) -> Message:
        user_id = decision.get("user_id", "unknown")
        self.log(f"[API] Processing cancellation for: {user_id} ...")

        result = self.api_simulator.cancel_reservation(user_id)
        if result["success"]:
            self.log(f"[API] Cancellation confirmed")
            self._send_notification(user_id, None, "cancelled")

            return Message(
                msg_id=f"exec-can-{message.msg_id}",
                msg_type=MessageType.EXECUTION_RESULT,
                sender=self.agent_id,
                recipient="user",
                content={"status": "success", "action": "cancel", "detail": result},
            )

        return self._error_response("No active reservation found for user", message)

    def _send_notification(self, user_id: str, seat_id: Optional[str], event: str):
        """Simulate sending a push notification to the user."""
        self.log(f"[API] Notification sent to {user_id}: reservation {event}")
        self.api_simulator.send_notification(user_id, event, seat_id)

    def _error_response(self, reason: str, message: Message) -> Message:
        return Message(
            msg_id=f"exec-err-{message.msg_id}",
            msg_type=MessageType.EXECUTION_RESULT,
            sender=self.agent_id,
            recipient="user",
            content={"status": "error", "reason": reason},
        )

    def get_stats(self) -> dict:
        return {
            "total_executions": len(self.execution_log),
            "successes": self.success_count,
            "failures": self.failure_count,
            "success_rate": f"{(self.success_count / max(1, self.success_count + self.failure_count) * 100):.1f}%",
        }


class APISimulator:
    """Simulates external API calls for the execution agent."""

    def check_availability(self, seat_id: str) -> bool:
        # The scheduler is the single source of truth for seat state in
        # this in-memory demo, so a seat it just allocated is always
        # available here. A real booking backend would be queried instead.
        return True

    def create_reservation(self, user_id: str, seat_id: str, decision: dict) -> dict:
        return {
            "success": True,
            "reservation_id": f"RSV-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            "seat_id": seat_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "duration_minutes": decision.get("duration_minutes", 120),
            "details": decision,
        }

    def release_seat(self, user_id: str) -> dict:
        return {"success": True, "user_id": user_id, "released_at": datetime.now().isoformat()}

    def cancel_reservation(self, user_id: str) -> dict:
        return {"success": True, "user_id": user_id, "cancelled_at": datetime.now().isoformat()}

    def send_notification(self, user_id: str, event: str, seat_id: Optional[str]):
        pass  # Simulated side effect
