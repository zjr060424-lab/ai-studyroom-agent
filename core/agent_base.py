from abc import ABC, abstractmethod
from typing import List, Optional
from core.message import Message, MessageType


class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str, description: str = ""):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.message_queue: List[Message] = []
        self.memory: dict = {}

    @abstractmethod
    def process(self, message: Message) -> Optional[Message]:
        """Process an incoming message and optionally return a response."""
        pass

    def receive(self, message: Message):
        """Receive a message and add it to the queue."""
        self.message_queue.append(message)

    def tick(self):
        """Process one message from the queue."""
        if self.message_queue:
            msg = self.message_queue.pop(0)
            return self.process(msg)
        return None

    def log(self, message: str, level: str = "INFO"):
        """Log a message with agent prefix."""
        print(f"  [{self.agent_id}] [{level}] {message}")

    def store_memory(self, key: str, value):
        self.memory[key] = value

    def recall_memory(self, key: str, default=None):
        return self.memory.get(key, default)
