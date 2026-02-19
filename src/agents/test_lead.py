"""Multi-Agent QA System - Test Lead Agent"""
import re
from typing import Any

from .base_agent import BaseAgent, AgentOutput
from ..core.prompts import load_prompt


class TestLeadAgent(BaseAgent):
    """
    Test Lead Agent
    
    Responsibilities:
    - Create System Test Execution Plan (STEP)
    - Create Test Plan
    """
    
    def __init__(self, agent_id: str = "tl"):
        from ..core.schemas import TestLeadOutput
        super().__init__(agent_id=agent_id, output_schema=TestLeadOutput)
        
    @property
    def allowed_inputs(self) -> list[str]:
        return ["test_strategy"]
    
    @property
    def allowed_outputs(self) -> list[str]:
        return ["step.md", "test_plan.md"]
    
    def _build_system_prompt(self) -> str:
        template = load_prompt("tl_system")
        return template.replace("{name}", self.name)

    def _build_user_prompt(self, input_data: dict[str, Any]) -> str:
        test_strategy = input_data.get("test_strategy", "")
        template = load_prompt("tl_user")
        return template.replace("{test_strategy}", test_strategy)
        
    # Reverting to base JSON parsing
    # def _parse_output(self, raw_output: str) -> Any:
    #     ...
