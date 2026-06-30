from smolagents import CodeAgent
from config import MODEL
from tools import ALL_TOOLS


def build_agent(max_steps: int = 6) -> CodeAgent:
    return CodeAgent(
        tools=ALL_TOOLS,
        model=MODEL,
        max_steps=max_steps,
        additional_authorized_imports=[],
    )