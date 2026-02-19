from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.json import JSON

# Custom theme for agents
theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "error": "bold red",
    "agent": "bold blue",
    "thought": "italic green",
    "artifact": "bold yellow"
})

console = Console(theme=theme)

def log_agent_start(agent_name: str, role: str):
    console.print(Panel(f"[bold]{role}[/bold] ({agent_name})", title="🤖 Agent Active", border_style="blue"))

def log_thought(agent_name: str, chunk: str):
    # Retrieve the last printed line to avoid spamming distinct lines for tokens
    # For now, we'll just print cleaner chunks or accumulate them?
    # Tokens are too granular for terminal. We might want to just print "Thinking..." or buffer.
    pass 

def log_artifact(agent_name: str, filename: str, type: str):
    console.print(f"[artifact]📄 {agent_name} generated [bold]{filename}[/bold] ({type})[/artifact]")

def log_completion(agent_name: str, success: bool):
    if success:
        console.print(f"[bold green]✓ {agent_name} completed successfully[/bold green]")
    else:
        console.print(f"[bold red]✗ {agent_name} failed[/bold red]")

def log_json(data: dict, title: str = "Output"):
    console.print(Panel(JSON.from_data(data), title=title, border_style="green"))
