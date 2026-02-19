from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import (
    product_manager_node, 
    developer_node,
    reviewer_node,
    test_manager_node, 
    test_lead_node, 
    automation_qa_node, 
    manual_qa_node
)
from ..core.events import WorkflowEventType

def create_qa_graph(checkpointer=None, interrupt_before=None):
    """Create the QA Multi-Agent Graph."""
    
    # Initialize Graph
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("ProductManager", product_manager_node)
    workflow.add_node("Developer", developer_node)
    workflow.add_node("Reviewer", reviewer_node)
    workflow.add_node("TestManager", test_manager_node)
    workflow.add_node("TestLead", test_lead_node)
    workflow.add_node("AutomationQA", automation_qa_node)
    workflow.add_node("ManualQA", manual_qa_node)
    
    # Smart Start Routing
    def route_start(state: AgentState):
        mode = state.get("start_mode", "full")
        if mode == "tests_only":
            return "AutomationQA"
        elif mode == "sts_only":
            return "TestManager"
        return "ProductManager"

    workflow.add_conditional_edges(
        START,
        route_start,
        {
            "ProductManager": "ProductManager",
            "AutomationQA": "AutomationQA",
            "TestManager": "TestManager"
        }
    )
    workflow.add_edge("ProductManager", "Developer")
    workflow.add_edge("Developer", "Reviewer")
    
    # Conditional Edge for Review
    def route_review(state: AgentState):
        """Route based on review approval."""
        if state.get("review_approved"):
            return "TestManager"
        return "Developer"

    workflow.add_conditional_edges(
        "Reviewer",
        route_review,
        {
            "TestManager": "TestManager",
            "Developer": "Developer"
        }
    )
    
    workflow.add_edge("TestManager", "TestLead")
    
    # Parallel execution for testers
    workflow.add_edge("TestLead", "AutomationQA")
    workflow.add_edge("TestLead", "ManualQA")
    
    # End
    workflow.add_edge("AutomationQA", END)
    workflow.add_edge("ManualQA", END)
    
    return workflow
