from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
from enum import Enum


class MessageType(Enum):
    REQUEST = "request"
    ANALYSIS_RESULT = "analysis_result"
    SCHEDULE_DECISION = "schedule_decision"
    ANOMALY_ALERT = "anomaly_alert"
    EXECUTION_COMMAND = "execution_command"
    EXECUTION_RESULT = "execution_result"
    FEEDBACK = "feedback"
    STATUS_UPDATE = "status_update"
    LOG = "log"


@dataclass
class Message:
    msg_id: str
    msg_type: MessageType
    sender: str
    recipient: str
    content: dict
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 0  # higher = more urgent
    context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "msg_id": self.msg_id,
            "msg_type": self.msg_type.value,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority,
            "context": self.context,
        }

    def add_context(self, key: str, value: Any):
        self.context[key] = value
