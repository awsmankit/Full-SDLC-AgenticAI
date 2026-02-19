"""Multi-Agent QA System - Configuration"""
from pathlib import Path


# LLM Configuration
LLM_MODEL = "qwen2.5:7b"  # Options: qwen2.5:7b, qwen3:8b
CODING_LLM_MODEL = "qwen2.5-coder:7b"
LLM_BASE_URL = "http://localhost:11434"
LLM_TEMPERATURE = 0.7
LLM_NUM_CTX = 8192  # Context window size
PERSONALITY = "software"  # Default personality

# Project Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

# Artifact subdirectories
REQUIREMENTS_DIR = ARTIFACTS_DIR / "requirements"
TESTING_DIR = ARTIFACTS_DIR / "testing"
BUGS_DIR = ARTIFACTS_DIR / "bugs"

# Ensure directories exist
def ensure_directories():
    """Create all necessary directories."""
    for directory in [ARTIFACTS_DIR, REQUIREMENTS_DIR, TESTING_DIR, BUGS_DIR, SCHEMAS_DIR, PROMPTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


# Agent Configuration
AGENT_MAX_RETRIES = 3
AGENT_TIMEOUT_SECONDS = 120

AGENT_CONFIG = {
    "ProductManager": {"name": "Product Manager", "role": "Product Manager", "icon": "Bot"},
    "Developer": {"name": "Senior Developer", "role": "Developer", "icon": "Code"},
    "Reviewer": {"name": "Code Reviewer", "role": "Reviewer", "icon": "Eye"},
    "TestManager": {"name": "Test Manager", "role": "Test Manager", "icon": "Activity"},
    "TestLead": {"name": "Test Lead", "role": "Test Lead", "icon": "Zap"},
    "AutomationQA": {"name": "Automation QA", "role": "Automation QA", "icon": "Cpu"},
    "ManualQA": {"name": "Manual QA", "role": "Manual QA", "icon": "CheckCircle"},
}

# HITL Configuration
HITL_CONFIG = {
    "interrupt_before": ["Developer", "Reviewer", "TestManager", "TestLead", "AutomationQA", "ManualQA"]
}
