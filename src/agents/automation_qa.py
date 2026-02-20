"""Multi-Agent QA System - Automation QA Agent"""
import re
from typing import Any

from .base_agent import BaseAgent, AgentOutput
from ..core.prompts import load_prompt


class AutomationQAAgent(BaseAgent):
    """
    Automation QA Agent
    
    Responsibilities:
    - Implementation of automation scripts
    """
    
    def __init__(self, agent_id: str = "automation"):
        from ..core.schemas import AutomationOutput
        super().__init__(agent_id=agent_id, output_schema=AutomationOutput)
        
    @property
    def allowed_inputs(self) -> list[str]:
        return ["test_plan"]
    
    @property
    def allowed_outputs(self) -> list[str]:
        return ["automation_tests.py"]
    
    def _build_system_prompt(self) -> str:
        template = load_prompt("automation_qa_system")
        return template.replace("{name}", self.name)

    def _build_user_prompt(self, input_data: dict[str, Any]) -> str:
        test_plan = input_data.get("test_plan", "")
        template = load_prompt("automation_qa_user")
        return template.replace("{test_plan}", test_plan)
