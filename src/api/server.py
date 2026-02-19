from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import queue
from datetime import datetime
import orjson
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

# Database Path
DB_PATH = "data/checkpoints.sqlite"

# Create connection
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

# Global Checkpointer (SQLite Persistence)
checkpointer = SqliteSaver(conn)

from ..workflow.graph import create_qa_graph
from ..workflow.state import AgentState
from ..core.events import WorkflowEvent, WorkflowEventType, STOPPED_RUNS
from ..core.config import ARTIFACTS_DIR, HITL_CONFIG

from ..core.run_manager import save_run_metadata, list_all_runs, update_run_status

app = FastAPI(title="Multi-Agent QA System API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Event Queue (Thread-safe)
# Global event queue
event_queue = queue.Queue()

@app.post("/stop/{run_id}")
async def stop_workflow(run_id: str):
    """Signal a workflow to stop."""
    STOPPED_RUNS.add(run_id)
    update_run_status(run_id, "stopped")
    return {"status": "stopping", "run_id": run_id}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(orjson.dumps(message).decode())
            except Exception:
                pass  # Handle disconnects gracefully

manager = ConnectionManager()

# Background task to process events from Queue -> WebSockets
async def event_processor():
    while True:
        try:
            if not event_queue.empty():
                event: WorkflowEvent = event_queue.get()
                await manager.broadcast(event.to_dict())
            else:
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in event processor: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(event_processor())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

class RunRequest(BaseModel):
    product_idea: str
    hitl_enabled: bool = False

class ResumeRequest(BaseModel):
    hitl_enabled: bool = True

def run_orchestrator(product_idea: str, run_id: str, hitl_enabled: bool):
# ... (rest of run_orchestrator remains same until graph creation)
    """Run LangGraph workflow in a thread."""
    
    # Save Metadata
    save_run_metadata(run_id, product_idea)
    
    # Structured Logging
    from ..core.log_manager import log_agent_start, log_completion, log_artifact, log_json

    def emit(type: WorkflowEventType, data: dict):
        # Inject run_id into event data for frontend correlation
        data["run_id"] = run_id
        
        # Thought Stream Unescaping (Affects both Terminal and UI)
        if type == WorkflowEventType.THOUGHT_CHUNK:
            chunk = data.get("chunk", "")
            if not hasattr(emit, "_buffer"): emit._buffer = ""
            emit._buffer += chunk
            
            if "\\" in emit._buffer:
                emit._buffer = emit._buffer.replace("\\n", "\n").replace('\\"', '"').replace("\\t", "\t")
            
            # Collapse multiple newlines (3+) into 2 to prevent huge gaps
            # We do this only on the unescaped buffer
            import re
            emit._buffer = re.sub(r'\n{3,}', '\n\n', emit._buffer)

            if not emit._buffer.endswith("\\"):
                # Update the chunk in data so UI gets the unescaped version
                data["chunk"] = emit._buffer
                print(emit._buffer, end="", flush=True)
                emit._buffer = ""
            else:
                # If we have a trailing backslash, it's a partial escape
                # Don't send this chunk yet, wait for the next part
                return

        event_queue.put(WorkflowEvent(type=type, data=data))
        
        # Other Terminal Output
        if type == WorkflowEventType.AGENT_START:
            log_agent_start(data.get("agent"), data.get("role"))
        elif type == WorkflowEventType.ARTIFACT_GENERATED:
            log_artifact(data.get("agent"), data.get("filename"), data.get("type"))
        elif type == WorkflowEventType.AGENT_COMPLETE:
            log_completion(data.get("agent"), data.get("success"))
        elif type == WorkflowEventType.WORKFLOW_COMPLETE:
            print("\n") # Newline after stream
            if data["status"] == "success":
                print("✓ Workflow Finished")
            else:
                print("✗ Workflow Error")
        
    try:
        emit(WorkflowEventType.WORKFLOW_START, {"product_idea": product_idea, "run_id": run_id})
        
        # Initial State
        initial_state: AgentState = {
            "run_id": run_id,
            "product_idea": product_idea,
            "mrs": None,
            "srs": None,
            "test_strategy": None,
            "step": None,
            "test_plan": None,
            "task_assignments": None,
            "automation_tests": None,
            "manual_tests": None,
            "bugs": [],
            "errors": [],
            "logs": []
        }
        
        # Determine interrupts
        interrupt_before = []
        if hitl_enabled:
            # Pause before Test Manager and Test Lead and Automation/Manual
            # interruption happens BEFORE the node executes.
            # We want to pause AFTER PM (before TestManager), AFTER TestManager (before TestLead)
            interrupt_before = HITL_CONFIG["interrupt_before"]
            
        graph = create_qa_graph(checkpointer=checkpointer, interrupt_before=interrupt_before)
        
        # Invoke with thread_id for persistence
        config = {"configurable": {"thread_id": run_id, "emitter": emit}}
        
        # Use invoke for synchronous execution derived from graph
        final_state = graph.invoke(initial_state, config=config)
        
        # Check if we finished or paused
        snapshot = graph.get_state(config)
        if snapshot.next:
            # We are paused
            emit(WorkflowEventType.WORKFLOW_PAUSED, {"next": snapshot.next})
            update_run_status(run_id, "paused")
        else:
            status = "success" if not final_state.get("errors") else "error"
            total_tokens = final_state.get("total_tokens", 0)
            
            emit(WorkflowEventType.WORKFLOW_COMPLETE, {"status": status, "total_tokens": total_tokens})
            update_run_status(run_id, status, total_tokens=total_tokens)
        
    except Exception as e:
        print(f"Graph execution failed: {e}")
        emit(WorkflowEventType.ERROR, {"message": str(e)})
        emit(WorkflowEventType.WORKFLOW_COMPLETE, {"status": "error"})
        update_run_status(run_id, "error")

@app.post("/run")
async def run_workflow(request: RunRequest, background_tasks: BackgroundTasks):
    """Start the multi-agent workflow."""
    # Generate Run ID with Product Slug
    import re
    slug = re.sub(r'[^a-zA-Z0-9]', '_', request.product_idea)[:30].strip('_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{timestamp}_{slug}"
    
    # Run in background thread to not block main loop
    background_tasks.add_task(run_orchestrator, request.product_idea, run_id, request.hitl_enabled)
    return {"status": "started", "run_id": run_id, "message": "Workflow started in background"}

@app.post("/resume/{run_id}")
async def resume_workflow(run_id: str, request: ResumeRequest, background_tasks: BackgroundTasks):
    """Resume a paused workflow."""
    
    def resume_task():
        # Re-create graph
        interrupt_before = HITL_CONFIG["interrupt_before"] if request.hitl_enabled else []
        graph = create_qa_graph(checkpointer=checkpointer, interrupt_before=interrupt_before)
        
        def emit(type: WorkflowEventType, data: dict):
            data["run_id"] = run_id
            
            # Thought Stream Unescaping
            if type == WorkflowEventType.THOUGHT_CHUNK:
                chunk = data.get("chunk", "")
                if not hasattr(emit, "_buffer"): emit._buffer = ""
                emit._buffer += chunk
                
                if "\\" in emit._buffer:
                    emit._buffer = emit._buffer.replace("\\n", "\n").replace('\\"', '"').replace("\\t", "\t")
                
                # Collapse multiple newlines
                import re
                emit._buffer = re.sub(r'\n{3,}', '\n\n', emit._buffer)

                if not emit._buffer.endswith("\\"):
                    data["chunk"] = emit._buffer
                    print(emit._buffer, end="", flush=True)
                    emit._buffer = ""
                else:
                    return

            event_queue.put(WorkflowEvent(type=type, data=data))

        config = {"configurable": {"thread_id": run_id, "emitter": emit}}
        
        try:
            # Resume by invoking with None (inputs are loaded from checkpoint)
            emit(WorkflowEventType.PHASE_START, {"phase": "Resuming Workflow", "agent": "System"})
            
            # Run the next step(s)
            final_state = graph.invoke(None, config=config)
            
            # Check status again
            snapshot = graph.get_state(config)
            if snapshot.next:
                emit(WorkflowEventType.WORKFLOW_PAUSED, {"next": snapshot.next})
                update_run_status(run_id, "paused")
            else:
                status = "success" if not final_state.get("errors") else "error"
                total_tokens = final_state.get("total_tokens", 0)
                emit(WorkflowEventType.WORKFLOW_COMPLETE, {"status": status, "total_tokens": total_tokens})
                update_run_status(run_id, status, total_tokens=total_tokens)
                
        except Exception as e:
            print(f"Resume failed: {e}")
            emit(WorkflowEventType.ERROR, {"message": str(e)})

    background_tasks.add_task(resume_task)
    return {"status": "resumed", "run_id": run_id}

@app.get("/runs")
async def list_runs():
    """List all available runs with metadata."""
    return {"runs": list_all_runs()}

@app.get("/agents")
async def get_agents():
    """Get agent configuration."""
    from ..core.config import AGENT_CONFIG
    return AGENT_CONFIG


@app.get("/runs/{run_id}/artifacts")
async def get_run_artifacts(run_id: str):
    """Get list of artifacts for a specific run."""
    run_dir = ARTIFACTS_DIR / run_id
    manifest_file = run_dir / "artifacts_manifest.json"
    
    if manifest_file.exists():
        try:
            manifest = orjson.loads(manifest_file.read_text())
            return {"artifacts": manifest}
        except:
            return {"artifacts": []}
    
    # Fallback to scanning if no manifest (for old runs)
    artifacts = []
    if run_dir.exists():
        for p in run_dir.rglob("*.md"):
            artifacts.append({
                "filename": p.name,
                "type": p.parent.name, # Use folder name as type
                "agent": "System (Legacy)",
                "timestamp": datetime.fromtimestamp(p.stat().st_mtime).strftime("%H:%M:%S")
            })
            
    return {"artifacts": artifacts}

@app.get("/artifact")
async def get_artifact(filename: str, run_id: Optional[str] = None):
    """Fetch artifact content by filename, optionally for a specific run."""
    try:
        # Search area
        search_dir = ARTIFACTS_DIR
        if run_id:
            search_dir = ARTIFACTS_DIR / run_id
            if not search_dir.exists():
                 return {"error": "Run ID not found", "content": ""}
        
        # Security check logic remains similar but scoped
        found = list(search_dir.rglob(filename))
        
        if not found:
            return {"error": "File not found", "content": ""}
        
        file_path = found[0]
        content = file_path.read_text(encoding="utf-8")
        return {"filename": filename, "content": content}
    except Exception as e:
        return {"error": str(e), "content": ""}
