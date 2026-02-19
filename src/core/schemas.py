from typing import List, Optional
from pydantic import BaseModel, Field

class ProductManagerOutput(BaseModel):
    mrs: str = Field(description="Market Requirements Specification (Markdown content)")
    srs: str = Field(description="Software Requirements Specification (Markdown content)")

class DeveloperOutput(BaseModel):
    code: str = Field(description="Source Code Explanation (Markdown content)")
    files: dict[str, str] = Field(description="Dictionary of filename to file content")

class ReviewerOutput(BaseModel):
    review: str = Field(description="Code Review Report (Markdown content)")
    approved: bool = Field(description="Whether the code is approved for testing")

class TestStrategyOutput(BaseModel):
    test_strategy: str = Field(description="Test Specification Document (Markdown content)")

class TestLeadOutput(BaseModel):
    step: str = Field(description="System Test Execution Plan (Markdown content)")
    test_plan: str = Field(description="Test Plan (Markdown content)")

class AutomationOutput(BaseModel):
    automation_tests: str = Field(description="Python Test Script (Code content)")

class ManualOutput(BaseModel):
    manual_tests: str = Field(description="Manual Test Cases (Markdown content)")
    bugs: Optional[str] = Field(default=None, description="Bug Reports (Markdown content, if any)")
