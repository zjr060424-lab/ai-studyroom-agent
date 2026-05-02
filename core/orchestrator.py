from typing import Dict, List, Optional, Type
from datetime import datetime
from core.message import Message, MessageType
from core.agent_base import BaseAgent


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

    def run_cycle(self, user_request: Optional[str] = None) -> List[Message]:
        """Run one full processing cycle through all agents."""
        self.step_count += 1
        responses = []

        if user_request:
            self.log(f"User Request: {user_request}")
            msg = Message(
                msg_id=f"req-{self.step_count}",
                msg_type=MessageType.REQUEST,
                sender="user",
                recipient="behavior_agent",
                content={"raw_request": user_request},
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
