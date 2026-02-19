"""Run Metadata Management"""
import orjson
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .config import ARTIFACTS_DIR

def save_run_metadata(run_id: str, product_idea: str):
    """Save metadata for a run."""
    run_dir = ARTIFACTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "id": run_id,
        "title": product_idea,
        "timestamp": datetime.now().isoformat(),
        "status": "running"
    }
    
    (run_dir / "run_metadata.json").write_bytes(orjson.dumps(metadata, option=orjson.OPT_INDENT_2))

def update_run_status(run_id: str, status: str, **kwargs):
    """Update the status of a run and other metadata."""
    run_dir = ARTIFACTS_DIR / run_id
    metadata_file = run_dir / "run_metadata.json"
    
    if metadata_file.exists():
        metadata = orjson.loads(metadata_file.read_text())
        metadata["status"] = status
        metadata["end_time"] = datetime.now().isoformat()
        metadata.update(kwargs)
        metadata_file.write_bytes(orjson.dumps(metadata, option=orjson.OPT_INDENT_2))

def get_run_metadata(run_id: str) -> Optional[Dict]:
    """Get metadata for a specific run."""
    metadata_file = ARTIFACTS_DIR / run_id / "run_metadata.json"
    if metadata_file.exists():
        return orjson.loads(metadata_file.read_text())
    return None

def list_all_runs() -> List[Dict]:
    """List all runs with metadata."""
    if not ARTIFACTS_DIR.exists():
        return []
        
    runs = []
    for run_dir in ARTIFACTS_DIR.iterdir():
        if run_dir.is_dir():
            metadata = get_run_metadata(run_dir.name)
            if metadata:
                runs.append(metadata)
            else:
                # Fallback for old runs without metadata
                runs.append({
                    "id": run_dir.name,
                    "title": f"Run {run_dir.name}",
                    "timestamp": datetime.fromtimestamp(run_dir.stat().st_mtime).isoformat(),
                    "status": "unknown"
                })
    
    # Sort by timestamp descending
    runs.sort(key=lambda x: x["timestamp"], reverse=True)
    return runs
