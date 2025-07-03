import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage


class BaseNode(ABC):
    """Simple base class for chatbot nodes"""

    def __init__(self, node_name: str, node_type: str):
        self.node_name = node_name
        self.node_type = node_type
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute node logic and return updated state"""
        pass

    def call_llm(self, messages: List[BaseMessage]) -> str:
        """Simple LLM call using Langchain with message history support"""

        response = self.llm.invoke(messages)
        return response.content.strip()

    def update_state(self, state: Dict[str, Any], **updates) -> Dict[str, Any]:
        """Update state with new values"""
        state.update(updates)
        return state
