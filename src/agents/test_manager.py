"""Multi-Agent QA System - Test Manager Agent"""
import re
from typing import Any

from .base_agent import BaseAgent, AgentOutput
from ..core.prompts import load_prompt


class TestManagerAgent(BaseAgent):
    """
    Test Manager Agent
    
    Responsibilities:
    - Create Test Specification (STS)
    - Define scope and out of scope
    - High-level planning
    """
    
    def __init__(self, agent_id: str = "tm"):
        from ..core.schemas import TestStrategyOutput
        super().__init__(agent_id=agent_id, output_schema=TestStrategyOutput)
        
    @property
    def allowed_inputs(self) -> list[str]:
        return ["srs"]
    
    @property
    def allowed_outputs(self) -> list[str]:
        return ["test_strategy.md"]
    
    def _build_system_prompt(self) -> str:
        template = load_prompt("tm_system")
        return template.replace("{name}", self.name)

    def _build_user_prompt(self, input_data: dict[str, Any]) -> str:
        srs = input_data.get("srs", "")
        template = load_prompt("tm_user")
        return template.replace("{srs_content}", srs)
