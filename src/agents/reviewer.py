"""Multi-Agent QA System - Reviewer Agent"""
from typing import Any

from .base_agent import BaseAgent
from ..core.prompts import load_prompt


class ReviewerAgent(BaseAgent):
    """
    Reviewer Agent
    
    Responsibilities:
    - Review code against SRS
    """
    
    def __init__(self, agent_id: str = "Reviewer"):
        from ..core.schemas import ReviewerOutput
        super().__init__(agent_id=agent_id, output_schema=ReviewerOutput)
        
    @property
    def allowed_inputs(self) -> list[str]:
        return ["srs", "code"]
    
    @property
    def allowed_outputs(self) -> list[str]:
        return ["code_review.md"]
    
    def _build_system_prompt(self) -> str:
        template = load_prompt("reviewer_system")
        return template.replace("{name}", self.name)

    def _build_user_prompt(self, input_data: dict[str, Any]) -> str:
        srs = input_data.get("srs", "")
        code = input_data.get("code", "")
        template = load_prompt("reviewer_user")
        return template.replace("{srs}", srs).replace("{code}", code)
