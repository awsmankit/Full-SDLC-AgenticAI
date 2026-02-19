from pathlib import Path
from . import config

def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from the prompts directory.
    Uses the configured PERSONALITY subfolder.
    
    Args:
        prompt_name: Name of the prompt file (without extension)
        
    Returns:
        Content of the prompt file
    """
    # 1. Try specific personality folder
    # Access PERSONALITY dynamically from config module
    prompt_path = config.PROMPTS_DIR / config.PERSONALITY / f"{prompt_name}.md"
    
    # 2. Fallback to generic if not found (optional, but good practice)
    # For now, we assume prompts exist in the specific personality folder
    
    if not prompt_path.exists():
        # Fallback to root (legacy support) or raise error
        # Try finding in root prompts/ (if we missed moving some)
        root_path = config.PROMPTS_DIR / f"{prompt_name}.md"
        if root_path.exists():
            return root_path.read_text(encoding="utf-8")
            
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
    return prompt_path.read_text(encoding="utf-8")
