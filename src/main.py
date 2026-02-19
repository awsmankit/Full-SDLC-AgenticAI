"""Multi-Agent QA System - CLI Entry Point"""
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from .workflow.graph import create_qa_graph
from .workflow.state import AgentState
from .core.events import WorkflowEventType
from .core.config import ensure_directories
import argparse

console = Console()


def main():
    """Main entry point for the Multi-Agent QA System."""
    parser = argparse.ArgumentParser(description="Multi-Agent QA System")
    parser.add_argument("idea", nargs="*", help="Product Idea")
    parser.add_argument("--mode", choices=["full", "tests_only", "sts_only"], default="full", help="Execution Mode")
    parser.add_argument("--personality", choices=["medical", "software"], default="software", help="Agent Personality")
    args = parser.parse_args()

    # Update Global Config
    from .core import config as cfg
    cfg.PERSONALITY = args.personality

    console.print(Panel(
        "[bold cyan]Multi-Agent QA System[/bold cyan]\n"
        "Powered by Ollama + Qwen\n"
        f"Personality: [bold green]{args.personality.upper()}[/bold green]\n\n"
        "[dim]Agents: Product Manager → Test Manager → ...[/dim]",
        title="🤖 Welcome",
        border_style="cyan"
    ))
    
    # Ensure directories exist
    ensure_directories()
    
    # Get product idea
    if args.idea:
        product_idea = " ".join(args.idea)
    else:
        product_idea = Prompt.ask(
            "\n[bold]Enter your product idea[/bold]",
            default="A simple todo app with user authentication"
        )
    
    if not product_idea.strip():
        console.print("[red]Error: Product idea cannot be empty[/red]")
        sys.exit(1)
        
    app_name = product_idea.split()[0:3] # simple heuristic
    app_name = "_".join(app_name).lower()
    
    # Initialize Checkpointer
    from langgraph.checkpoint.sqlite import SqliteSaver
    import sqlite3
    
    # Use a local SQLite file for checkpoints
    db_path = ".checkpoints.sqlite"
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)

    # Run LangGraph
    workflow = create_qa_graph()
    graph = workflow.compile(checkpointer=memory)
    
    # Define Thread ID for Persistence (Use app_name to resume)
    thread_id = app_name
    
    # Event handler for Console UI
    from .core.log_manager import log_agent_start, log_completion, log_artifact

    def emit(type: WorkflowEventType, data: dict):
        if type == WorkflowEventType.PHASE_START:
            console.print(f"\n[bold blue]═══ Phase: {data['phase']} ═══[/bold blue]\n")
        elif type == WorkflowEventType.AGENT_START:
            log_agent_start(data.get("agent"), data.get("role"))
        elif type == WorkflowEventType.THOUGHT_CHUNK:
            chunk = data.get("chunk", "")
            if not hasattr(emit, "_buffer"): emit._buffer = ""
            emit._buffer += chunk
            
            if "\\" in emit._buffer:
                emit._buffer = emit._buffer.replace("\\n", "\n").replace('\\"', '"').replace("\\t", "\t")
            
            # Collapse multiple newlines
            import re
            emit._buffer = re.sub(r'\n{3,}', '\n\n', emit._buffer)

            if not emit._buffer.endswith("\\"):
                # Use print for the stream, don't use console.print as it might add extra formatting/newlines
                print(emit._buffer, end="", flush=True)
                emit._buffer = ""
            else:
                return
        elif type == WorkflowEventType.ARTIFACT_GENERATED:
            log_artifact(data.get("agent"), data.get("filename"), data.get("type"))
        elif type == WorkflowEventType.AGENT_COMPLETE:
            log_completion(data.get("agent"), data.get("success"))
        elif type == WorkflowEventType.WORKFLOW_COMPLETE:
            print("\n")
            if data["status"] == "success":
                console.print(f"[bold green]Starting Workflow for: {app_name}[/bold green]")

    if args.mode != "full":
        console.print(f"[yellow]Mode: {args.mode}[/yellow]")

    # Initial State
    initial_state: AgentState = {
        "run_id": app_name, # Use app_name as run_id to group artifacts
        "product_idea": product_idea,
        "app_name": app_name,
        "start_mode": args.mode,
        "mrs": None,
        "srs": None,
        "test_strategy": None,
        "step": None,
        "test_plan": None,
        "task_assignments": None,
        "automation_tests": None,
        "manual_tests": None,
        "code": None,
        "review": None,
        "review_approved": False,
        "bugs": [],
        "errors": [],
        "logs": []
    }

    # Create Config with Thread ID and Emitter
    config = {"configurable": {"thread_id": thread_id, "emitter": emit}}
    
    # Check for existing state
    snapshot = graph.get_state(config)
    if snapshot.values and snapshot.next:
        console.print(f"[yellow]Resuming existing workflow (Thread: {thread_id})...[/yellow]")
        final_state = graph.invoke(None, config=config)
    else:
        # Invoke Graph with initial state
        final_state = graph.invoke(initial_state, config=config)
    
    # Exit code based on success
    sys.exit(0 if not final_state.get("errors") else 1)


if __name__ == "__main__":
    main()
