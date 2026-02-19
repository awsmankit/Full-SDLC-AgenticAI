"""Multi-Agent QA System - LLM Integration"""
from langchain_ollama import ChatOllama
from rich.console import Console
from typing import Optional, Callable

from .config import LLM_MODEL, LLM_BASE_URL, LLM_TEMPERATURE, LLM_NUM_CTX

console = Console()


def get_llm(model_name: str = LLM_MODEL) -> ChatOllama:
    """Get configured Ollama LLM instance."""
    return ChatOllama(
        model=model_name,
        base_url=LLM_BASE_URL,
        temperature=LLM_TEMPERATURE,
        num_ctx=LLM_NUM_CTX,
    )


def invoke_llm(llm: ChatOllama, messages: list[dict]) -> str:
    """
    Invoke LLM with messages and return response.
    
    Args:
        llm: ChatOllama instance
        messages: List of message dicts with 'role' and 'content'
        
    Returns:
        LLM response content as string
    """
    try:
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        console.print(f"[red]LLM Error: {e}[/red]")
        raise


def stream_llm(llm: ChatOllama, messages: list[dict], on_token: Optional[Callable[[str], None]] = None) -> tuple[str, dict]:
    """
    Stream LLM response to console and return full content with usage stats.
    
    Args:
        llm: ChatOllama instance
        messages: List of message dicts
        
    Returns:
        Tuple of (Full response content, Usage dict)
    """
    full_response = ""
    usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    
    try:
        # Stream chunks
        for chunk in llm.stream(messages):
            content = chunk.content
            if content:
                full_response += content
                if on_token:
                    on_token(content)
            
            # Capture usage if available (usually in the last chunk)
            if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                usage = chunk.usage_metadata
                
        console.print()  # Newline at end
        return full_response, usage
        
    except Exception as e:
        console.print(f"[red]LLM Streaming Error: {e}[/red]")
        raise
