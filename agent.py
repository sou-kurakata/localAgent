from smolagents import ToolCallingAgent
from config import MODEL
from tools import ALL_TOOLS


def build_agent(max_steps: int = 6) -> ToolCallingAgent:
    return ToolCallingAgent(
        tools=ALL_TOOLS,
        model=MODEL,
        max_steps=max_steps,
    )