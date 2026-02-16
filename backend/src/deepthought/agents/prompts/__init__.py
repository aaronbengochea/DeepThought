"""Agent system prompts for the DeepThought multi-agent system."""

from deepthought.agents.prompts.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
from deepthought.agents.prompts.execution import EXECUTION_SYSTEM_PROMPT
from deepthought.agents.prompts.verification import VERIFICATION_SYSTEM_PROMPT
from deepthought.agents.prompts.response import RESPONSE_SYSTEM_PROMPT

__all__ = [
    "ORCHESTRATOR_SYSTEM_PROMPT",
    "EXECUTION_SYSTEM_PROMPT",
    "VERIFICATION_SYSTEM_PROMPT",
    "RESPONSE_SYSTEM_PROMPT",
]
