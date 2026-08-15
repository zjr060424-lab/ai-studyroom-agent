from typing import Dict, List, Optional
from datetime import datetime
from core.message import Message, MessageType
from core.agent_base import BaseAgent

# Message types that the anomaly detector passively observes.
MONITORED_TYPES = (MessageType.ANALYSIS_RESULT, MessageType.SCHEDULE_DECISION)
OBSERVER_AGENT_ID = "anomaly_agent"


class Orchestrator:
    """Central orchestrator that coordinates multi-agent collaboration."""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_log: List[Message] = []
        self.global_context: dict = {}
        self.step_count: int = 0

    def register_agent(self, agent: BaseAgent):
        self.agents[agent.agent_id] = agent
        self.log(f"Agent registered: {agent.name} ({agent.agent_id})")

    def send_message(self, message: Message):
        self.message_log.append(message)

        # If broadcast to all
        if message.recipient == "*":
            for agent in self.agents.values():
                agent.receive(message)
            return

        # Send to specific agent
        recipient = self.agents.get(message.recipient)
        if recipient:
            recipient.receive(message)
        else:
            self.log(f"No agent found with id: {message.recipient}", "WARNING")

        # Mirror pipeline traffic to the anomaly detector so it can monitor
        # user activity patterns without being a direct recipient.
        observer = self.agents.get(OBSERVER_AGENT_ID)
        if (observer
                and message.msg_type in MONITORED_TYPES
                and message.sender != OBSERVER_AGENT_ID
                and message.recipient != OBSERVER_AGENT_ID):
            observer.receive(message)

    def run_cycle(self, user_request: Optional[str] = None,
                  meta: Optional[dict] = None) -> List[Message]:
        """Run one full processing cycle through all agents.

        Args:
            user_request: Raw natural-language request text.
            meta: Optional structured fields (e.g. user_id, duration_minutes,
                preferred_area) that override values parsed from the text.
        """
        self.step_count += 1
        responses = []

        if user_request:
            self.log(f"User Request: {user_request}")
            content = {"raw_request": user_request}
            if meta:
                content.update({k: v for k, v in meta.items() if v is not None})
            msg = Message(
                msg_id=f"req-{self.step_count}",
                msg_type=MessageType.REQUEST,
                sender="user",
                recipient="behavior_agent",
                content=content,
            )
            self.send_message(msg)

        # Process each agent in sequence
        pipeline = ["behavior_agent", "anomaly_agent", "scheduler_agent", "executor_agent"]

        for agent_id in pipeline:
            agent = self.agents.get(agent_id)
            if agent:
                result = agent.tick()
                if result:
                    responses.append(result)
                    if result.recipient != "user":
                        self.send_message(result)

        return responses

    def log(self, message: str, level: str = "INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        icon = {
            "INFO": "[Orchestrator]",
            "WARNING": "[Orchestrator] [WARN]",
            "ERROR": "[Orchestrator] [ERROR]",
            "SUCCESS": "[Orchestrator] [OK]",
        }.get(level, "[Orchestrator]")
        print(f"  {icon} {message}")

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        return self.agents.get(agent_id)

    def summarize(self) -> dict:
        return {
            "cycle": self.step_count,
            "agents": len(self.agents),
            "messages_processed": len(self.message_log),
            "context_keys": list(self.global_context.keys()),
        }
