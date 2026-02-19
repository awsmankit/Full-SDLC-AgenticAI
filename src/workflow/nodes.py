from typing import Dict, Any
from langchain_core.runnables import RunnableConfig

from .state import AgentState
from ..agents import ProductManagerAgent, TestManagerAgent, TestLeadAgent, AutomationQAAgent, ManualQAAgent, DeveloperAgent, ReviewerAgent
from ..core.events import WorkflowEventType, STOPPED_RUNS
from ..core.artifacts import save_artifact, get_artifact_info

# ... (agents init remains same)

def _check_stopped(state: AgentState):
    """Raise error if run was stopped."""
    run_id = state.get("run_id")
    if run_id in STOPPED_RUNS:
        # Clear from registry after stopping
        STOPPED_RUNS.discard(run_id)
        raise InterruptedError(f"Workflow execution for {run_id} was stopped by user.")

# Initialize agents
pm_agent = ProductManagerAgent(agent_id="ProductManager")
dev_agent = DeveloperAgent(agent_id="Developer")
reviewer_agent = ReviewerAgent(agent_id="Reviewer")
tm_agent = TestManagerAgent(agent_id="TestManager")
tl_agent = TestLeadAgent(agent_id="TestLead")
automation_agent = AutomationQAAgent(agent_id="AutomationQA")
manual_agent = ManualQAAgent(agent_id="ManualQA")

def _emit(config: RunnableConfig, event_type: WorkflowEventType, data: Dict[str, Any]):
    """Helper to emit events."""
    emitter = config.get("configurable", {}).get("emitter")
    if emitter:
        emitter(event_type, data)

def _get_on_token(config: RunnableConfig, agent_id: str, run_id: str):
    """Generic token streamer with interrupt check."""
    def on_token(token):
        if run_id in STOPPED_RUNS:
            # Clear from registry after stopping to allow future fresh runs if needed
            # (though usually run_id is unique)
            STOPPED_RUNS.discard(run_id)
            raise InterruptedError(f"Workflow execution for {run_id} stopped via token stream.")
        _emit(config, WorkflowEventType.THOUGHT_CHUNK, {"agent": agent_id, "chunk": token})
    return on_token

def _handle_agent_output(state: AgentState, config: RunnableConfig, output: Any, agent_id: str) -> Dict[str, Any]:
    """Generic agent output processor."""
    _emit(config, WorkflowEventType.AGENT_COMPLETE, {"agent": agent_id, "success": output.success})
    
    if not output.success:
        return {"errors": output.errors, "total_tokens": output.token_usage.get("total_tokens", 0)}
        
    updates = {"total_tokens": output.token_usage.get("total_tokens", 0)}
    run_id = state.get("run_id")
    
    for key, content in output.artifacts.items():
        if not content: continue
        
        # Skip non-string content (e.g. file dicts which are handled by specific nodes)
        if not isinstance(content, str):
            continue
            
        filename, category = get_artifact_info(key)
        
        # Emit artifact event
        _emit(config, WorkflowEventType.ARTIFACT_GENERATED, {
            "filename": filename, 
            "type": category, 
            "agent": agent_id
        })
        
        # Save to disk
        save_artifact(content, filename, category, run_id, agent_name=agent_id)
        
        # Add to state updates
        if key in state:
            if key == "bugs":
                updates["bugs"] = [content] if isinstance(content, str) else content
            else:
                updates[key] = content
    
    # Handle non-artifact fields from output (like 'approved')
    if hasattr(output, "artifacts") and isinstance(output.artifacts, dict):
        if "approved" in output.artifacts:
             updates["review_approved"] = output.artifacts["approved"]

    return updates

def product_manager_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Node for ProductManager."""
    _check_stopped(state)
    agent_id = "ProductManager"
    _emit(config, WorkflowEventType.PHASE_START, {"phase": "Requirements Creation", "agent": agent_id})
    _emit(config, WorkflowEventType.AGENT_START, {"agent": agent_id, "role": "Product Manager"})
    
    output = pm_agent.invoke({"product_idea": state["product_idea"]}, on_token=_get_on_token(config, agent_id, state.get("run_id", "default")))
    return _handle_agent_output(state, config, output, agent_id)

def test_manager_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Node for TestManager."""
    _check_stopped(state)
    agent_id = "TestManager"
    _emit(config, WorkflowEventType.PHASE_START, {"phase": "Test Specification Creation", "agent": agent_id})
    _emit(config, WorkflowEventType.AGENT_START, {"agent": agent_id, "role": "Test Manager"})
    
    output = tm_agent.invoke({"srs": state["srs"]}, on_token=_get_on_token(config, agent_id, state.get("run_id", "default")))
    return _handle_agent_output(state, config, output, agent_id)

def test_lead_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Node for TestLead."""
    _check_stopped(state)
    agent_id = "TestLead"
    _emit(config, WorkflowEventType.PHASE_START, {"phase": "Test Planning", "agent": agent_id})
    _emit(config, WorkflowEventType.AGENT_START, {"agent": agent_id, "role": "Test Lead"})
    
    output = tl_agent.invoke({"test_strategy": state["test_strategy"]}, on_token=_get_on_token(config, agent_id, state.get("run_id", "default")))
    return _handle_agent_output(state, config, output, agent_id)

def automation_qa_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Node for AutomationQA."""
    _check_stopped(state)
    agent_id = "AutomationQA"
    _emit(config, WorkflowEventType.AGENT_START, {"agent": agent_id, "role": "Automation QA"})
    
    test_plan_input = state.get("step") or state.get("test_plan")
    output = automation_agent.invoke({"test_plan": test_plan_input}, on_token=_get_on_token(config, agent_id, state.get("run_id", "default")))
    
    # Write test file
    if output.success and output.artifacts:
        import os
        from ..core.config import PROJECT_ROOT, ARTIFACTS_DIR
        
        # Use sanitized app name for directory
        app_name = state.get("app_name", "generated_app").replace(" ", "_").lower()
        app_dir = PROJECT_ROOT / app_name
        app_dir.mkdir(exist_ok=True)
        
        # Save automation_tests content
        if "automation_tests" in output.artifacts:
             test_content = output.artifacts["automation_tests"]
             # Use ARTIFACTS_DIR / run_id / tests
             from ..core.config import ARTIFACTS_DIR
             run_id = state.get("run_id", "default_run")
             test_dir = ARTIFACTS_DIR / run_id / "tests"
             test_dir.mkdir(parents=True, exist_ok=True)
             
             file_path = test_dir / "test_app.py"
             file_path.write_text(test_content, encoding="utf-8")
             _emit(config, WorkflowEventType.ARTIFACT_GENERATED, {
                "filename": str(file_path.relative_to(PROJECT_ROOT)), 
                "type": "Automation Logic", 
                "agent": agent_id
            })

    return _handle_agent_output(state, config, output, agent_id)

def manual_qa_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Node for ManualQA."""
    _check_stopped(state)
    agent_id = "ManualQA"
    _emit(config, WorkflowEventType.AGENT_START, {"agent": agent_id, "role": "Manual QA"})
    
    test_plan_input = state.get("step") or state.get("test_plan")
    output = manual_agent.invoke({"test_plan": test_plan_input}, on_token=_get_on_token(config, agent_id, state.get("run_id", "default")))
    return _handle_agent_output(state, config, output, agent_id)

def developer_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Node for Developer."""
    _check_stopped(state)
    agent_id = "Developer"
    _emit(config, WorkflowEventType.PHASE_START, {"phase": "Development", "agent": agent_id})
    _emit(config, WorkflowEventType.AGENT_START, {"agent": agent_id, "role": "Senior Developer"})

    output = dev_agent.invoke({"srs": state["srs"], "review": state.get("review")}, on_token=_get_on_token(config, agent_id, state.get("run_id", "default")))
    
    # Write files to disk
    if output.success and isinstance(output.artifacts, dict) and "files" in output.artifacts:
        from ..core.config import ARTIFACTS_DIR, PROJECT_ROOT
        
        # Use ARTIFACTS_DIR / run_id / src
        run_id = state.get("run_id", "default_run")
        src_dir = ARTIFACTS_DIR / run_id / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        
        files = output.artifacts["files"]
        for filename, content in files.items():
            file_path = src_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            _emit(config, WorkflowEventType.ARTIFACT_GENERATED, {
                "filename": str(file_path.relative_to(PROJECT_ROOT)), 
                "type": "Source Code", 
                "agent": agent_id
            })

    return _handle_agent_output(state, config, output, agent_id)

def reviewer_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Node for Reviewer."""
    _check_stopped(state)
    agent_id = "Reviewer"
    _emit(config, WorkflowEventType.PHASE_START, {"phase": "Code Review", "agent": agent_id})
    _emit(config, WorkflowEventType.AGENT_START, {"agent": agent_id, "role": "Code Reviewer"})

    output = reviewer_agent.invoke({"srs": state["srs"], "code": state["code"]}, on_token=_get_on_token(config, agent_id, state.get("run_id", "default")))
    return _handle_agent_output(state, config, output, agent_id)
