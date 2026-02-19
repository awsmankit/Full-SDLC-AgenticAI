"""Multi-Agent QA System - Developer Agent"""
from typing import Any

from .base_agent import BaseAgent
from ..core.prompts import load_prompt
from ..core.config import CODING_LLM_MODEL
from ..core.llm import get_llm
from ..core.schemas import DeveloperOutput
import re


class DeveloperAgent(BaseAgent):
    """
    Developer Agent
    
    Responsibilities:
    - Create implementation skeleton based on SRS
    - Use Python + Streamlit
    - Iterate based on review feedback
    """
    
    def __init__(self, agent_id: str = "Developer"):
        from ..core.schemas import DeveloperOutput
        super().__init__(agent_id=agent_id, output_schema=DeveloperOutput)
        
        # Override LLM with coding model
        self.llm = get_llm(model_name=CODING_LLM_MODEL)
        
    # Reverting to base JSON parsing
    # def _parse_output(self, raw_output: str) -> DeveloperOutput:
    #     ...
        
    @property
    def allowed_inputs(self) -> list[str]:
        return ["srs", "review"]
    
    @property
    def allowed_outputs(self) -> list[str]:
        return ["source_code.md"]
    
    def _build_system_prompt(self) -> str:
        template = load_prompt("dev_system")
        return template.replace("{name}", self.name)

    def _build_user_prompt(self, input_data: dict[str, Any]) -> str:
        srs = input_data.get("srs", "")
        review = input_data.get("review", "")
        
        template = load_prompt("dev_user")
        
        if review:
            # Add review feedback to the prompt
            template += f"\n\nPrevious Review Feedback:\n{review}\n\nPlease fix the issues and provide updated code."
            
        return template.replace("{srs}", srs)
