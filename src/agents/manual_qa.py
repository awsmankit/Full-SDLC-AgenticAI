"""Multi-Agent QA System - Manual QA Agent"""
import re
from typing import Any

from .base_agent import BaseAgent, AgentOutput
from ..core.prompts import load_prompt


class ManualQAAgent(BaseAgent):
    """
    Manual QA Agent
    
    Responsibilities:
    - Execute manual test cases
    - Report bugs
    """
    
    def __init__(self, agent_id: str = "manual"):
        from ..core.schemas import ManualOutput
        super().__init__(agent_id=agent_id, output_schema=ManualOutput)
        
    @property
    def allowed_inputs(self) -> list[str]:
        return ["test_plan"]
    
    @property
    def allowed_outputs(self) -> list[str]:
        return ["manual_test_cases.md"]
    
    def _build_system_prompt(self) -> str:
        template = load_prompt("manual_qa_system")
        return template.replace("{name}", self.name)

    def _build_user_prompt(self, input_data: dict[str, Any]) -> str:
        test_plan = input_data.get("test_plan", "")
        
        template = load_prompt("manual_qa_user")
        return template.replace("{test_plan}", test_plan)
