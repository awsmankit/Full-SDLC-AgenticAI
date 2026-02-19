from typing import TypedDict, Annotated, List, Dict, Any, Optional
import operator

class AgentState(TypedDict):
    """
    State passed between nodes in the LangGraph workflow.
    """
    run_id: str
    # Inputs
    product_idea: str
    
    # Artifacts
    mrs: Optional[str]
    srs: Optional[str]
    test_strategy: Optional[str]
    step: Optional[str]
    automation_tests: Optional[str]
    manual_tests: Optional[str]
    code: Optional[str]
    review: Optional[str]
    review_approved: Optional[bool]
    
    # Execution Control
    app_name: str
    start_mode: str  # 'full', 'sts_only', 'tests_only'
    
    # Shared Data
    bugs: Annotated[List[str], operator.add]
    errors: Annotated[List[str], operator.add]
    
    # Metadata for UI
    logs: Annotated[List[str], operator.add]
    total_tokens: Annotated[int, operator.add]
