"""Multi-Agent QA System - Product Manager Agent"""
import re
from typing import Any

from .base_agent import BaseAgent, AgentOutput
from ..core.prompts import load_prompt


class ProductManagerAgent(BaseAgent):
    """
    Product Manager Agent
    
    Responsibilities:
    - Understand business ideas
    - Create MRS (Market Requirements Specification)
    - Create SRS (Software Requirements Specification)
    - Clarify assumptions
    - Never write test cases
    """
    
    # Remove hardcoded name/role - served by BaseAgent from config
    # name = "Aishwarya" 
    # role = "Senior Product Manager"
    
    def __init__(self, agent_id: str = "pm"):
        from ..core.schemas import ProductManagerOutput
        super().__init__(agent_id=agent_id, output_schema=ProductManagerOutput)
        
    @property
    def allowed_inputs(self) -> list[str]:
        return ["product_idea"]
    
    @property
    def allowed_outputs(self) -> list[str]:
        return ["mrs.md", "srs.md"]
    
    def _build_system_prompt(self) -> str:
        template = load_prompt("pm_system")
        return template.replace("{name}", self.name)

    def _build_user_prompt(self, input_data: dict[str, Any]) -> str:
        product_idea = input_data.get("product_idea", "")
        template = load_prompt("pm_user")
        return template.replace("{product_idea}", product_idea)
