"""Multi-Agent QA System - Artifact Storage"""
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import ARTIFACTS_DIR, REQUIREMENTS_DIR, TESTING_DIR, BUGS_DIR, ensure_directories


import orjson

# Centralized Mapping for Artifacts
# Output Key -> (Target Filename, Category)
ARTIFACT_MAP = {
    "mrs": ("MRS.md", "requirements"),
    "srs": ("SRS.md", "requirements"),
    "test_strategy": ("STS.md", "testing"),
    "step": ("STEP.md", "testing"),
    "test_plan": ("Test_Plan.md", "testing"),
    "automation_tests": ("Automation_Tests.py", "testing"),
    "manual_tests": ("Manual_Test_Cases.md", "testing"),
    "bugs": ("Bugs.md", "bugs"),
}

def get_artifact_info(key: str) -> tuple[str, str]:
    """Get mapping info for an artifact key."""
    return ARTIFACT_MAP.get(key, (f"{key}.txt", "requirements"))

def save_artifact(content: str, filename: str, category: str = "requirements", run_id: Optional[str] = None, agent_name: Optional[str] = None) -> Path:
    """
    Save an artifact to the appropriate directory.
    
    Args:
        content: The content to save
        filename: Name of the file (e.g., 'mrs.md')
        category: One of 'requirements', 'testing', 'bugs'
        run_id: Optional run ID to separate sessions
        agent_name: Name of the agent generating the artifact
        
    Returns:
        Path to the saved file
    """
    ensure_directories()
    
    # Base directory
    base_dir = ARTIFACTS_DIR
    manifest_file = None
    
    if run_id:
        base_dir = ARTIFACTS_DIR / run_id
        base_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = base_dir / "artifacts_manifest.json"
    
    category_dirs = {
        "requirements": base_dir / "requirements",
        "testing": base_dir / "testing",
        "bugs": base_dir / "bugs",
    }
    
    directory = category_dirs.get(category, base_dir / "requirements")
    directory.mkdir(parents=True, exist_ok=True) # Ensure subdir exists
    filepath = directory / filename
    
    # Add timestamp header
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # filepath.write_text(header + content, encoding="utf-8")
    filepath.write_text(content, encoding="utf-8")
    
    # Update Manifest
    if manifest_file:
        manifest = []
        if manifest_file.exists():
            try:
                manifest = orjson.loads(manifest_file.read_text())
            except:
                pass
        
        # Check if exists and update, or append
        artifact_entry = {
            "filename": filename,
            "type": category,
            "agent": agent_name or "System",
            "timestamp": timestamp,
            "path": str(filepath.relative_to(base_dir))
        }
        
        # Remove existing entry for same filename if any (overwrite)
        manifest = [m for m in manifest if m["filename"] != filename]
        manifest.append(artifact_entry)
        
        manifest_file.write_bytes(orjson.dumps(manifest, option=orjson.OPT_INDENT_2))
        
    return filepath


def load_artifact(filename: str, category: str = "requirements") -> Optional[str]:
    """
    Load an artifact from the appropriate directory.
    
    Args:
        filename: Name of the file
        category: One of 'requirements', 'testing', 'bugs'
        
    Returns:
        File content as string, or None if not found
    """
    category_dirs = {
        "requirements": REQUIREMENTS_DIR,
        "testing": TESTING_DIR,
        "bugs": BUGS_DIR,
    }
    
    directory = category_dirs.get(category, REQUIREMENTS_DIR)
    filepath = directory / filename
    
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return None


def list_artifacts(category: str = "requirements") -> list[str]:
    """List all artifacts in a category."""
    category_dirs = {
        "requirements": REQUIREMENTS_DIR,
        "testing": TESTING_DIR,
        "bugs": BUGS_DIR,
    }
    
    directory = category_dirs.get(category, REQUIREMENTS_DIR)
    
    if not directory.exists():
        return []
    
    return [f.name for f in directory.glob("*.md")]
