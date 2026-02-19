from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any

class WorkflowEventType(Enum):
    """Types of events emitted by the orchestrator."""
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_PAUSED = "workflow_paused"
    PHASE_START = "phase_start"
    PHASE_COMPLETE = "phase_complete"
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"
    ARTIFACT_GENERATED = "artifact_generated"
    THOUGHT_CHUNK = "thought_chunk"
    ERROR = "error"

# Track which runs have been requested to stop
STOPPED_RUNS = set()


@dataclass
class WorkflowEvent:
    """Event emitted during workflow execution."""
    type: WorkflowEventType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }
