"""Multi-Agent QA System - Base Agent Class"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Callable

import re
import orjson
from ..core.llm import get_llm, stream_llm


@dataclass
class AgentOutput:
    """Structured output from an agent."""
    success: bool
    artifacts: dict[str, str] = field(default_factory=dict)  # filename -> content
    message: str = ""
    errors: list[str] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=lambda: {"total_tokens": 0})


class BaseAgent(ABC):
    """
    Base class for all QA agents.
    
    Each agent has:
    - A specific role and responsibilities
    - A system prompt defining their behavior
    - Allowed inputs and outputs
    - Methods to process inputs and generate outputs
    """
    
    name: str = "Agent"
    role: str = "Generic Agent"
    
    def __init__(self, agent_id: Optional[str] = None, output_schema: Optional[Any] = None):
        self.llm = get_llm()
        self.agent_id = agent_id
        self.output_schema = output_schema
        
        # Load config if agent_id is provided
        if agent_id:
            from ..core.config import AGENT_CONFIG
            if agent_id in AGENT_CONFIG:
                cfg = AGENT_CONFIG[agent_id]
                self.name = cfg["name"]
                self.role = cfg["role"]
                
        self._system_prompt = self._build_system_prompt()
        if self.output_schema:
             self._system_prompt += "\n\nCRITICAL: You must respond with a raw JSON object wrapped in a markdown code block: ```json { ... } ```. \n" \
                                    f"Required JSON Schema: {self.output_schema.model_json_schema()}"

    @property
    @abstractmethod
    def allowed_inputs(self) -> list[str]:
        """List of artifact types this agent can accept as input."""
        pass
    
    @property
    @abstractmethod
    def allowed_outputs(self) -> list[str]:
        """List of artifact types this agent produces."""
        pass
    
    @abstractmethod
    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent."""
        pass
    
    @abstractmethod
    def _build_user_prompt(self, input_data: dict[str, Any]) -> str:
        """Build the user prompt from input data."""
        pass
    
    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON block from text using multiple strategies."""
        # Clean the text slightly to handle common LLM garbage
        text = text.strip()

        # Specification 1: Look for any curly brace block using brace counting (most robust for nested blocks)
        start = text.find('{')
        if start != -1:
            count = 0
            # Walk through the text and find the matching closing brace
            for i in range(start, len(text)):
                if text[i] == '{':
                    count += 1
                elif text[i] == '}':
                    count -= 1
                    if count == 0:
                        candidate = text[start:i+1]
                        # Final check: does it look like JSON?
                        if '"' in candidate and ':' in candidate:
                            return candidate

        # Specification 2: Look for markdown code blocks (fallback if counting fails for some weird reason)
        json_blocks = re.findall(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_blocks:
            for block in reversed(json_blocks):
                cleaned = block.strip()
                if cleaned.startswith('{') and cleaned.endswith('}'):
                    return cleaned

        return None

    def _fix_json(self, json_str: str) -> str:
        """Attempt to fix common JSON errors from LLMs."""
        # Clean up some common markdown/text artifacts
        json_str = json_str.strip()
        
        # 1. Handle trailing commas
        json_str = re.sub(r',\s*\}', '}', json_str)
        json_str = re.sub(r',\s*\]', ']', json_str)

        # 2. Aggressive Newline Escaping
        # If we fail to parse, it's often because of unescaped newlines inside strings.
        # This regex looks for a line that does NOT end with a valid JSON delimiter 
        # (comma, opening/closing brace/bracket) and joins it with the next line.
        # This is risky but often necessary for code generation.
        
        # Let's try a safer approach first: replace newlines that are clearly inside strings?
        # No, that's hard.
        
        # Let's try this: detailed error analysis usually shows where it failed.
        # But we don't have the error offset easily available here.
        
        # Heuristic: If a line ends with a " or , or structure char, it's probably fine.
        # If it ends with text, it's probably a continuation.
        
        lines = json_str.split('\n')
        fixed_lines = []
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            # If line is empty, just keep it (it might be formatting)
            if not stripped:
                fixed_lines.append(line)
                continue
                
            # Heuristic: Valid JSON lines usually end with:
            # - , (comma)
            # - { or [ (opening structure)
            # - } or ] (closing structure)
            # - " (end of string value)
            # - true/false/null/number
            
            # If a line ends with none of these, it's likely a string continuation that needs an escaped newline.
            # AND the previous line likely ended with an opening quote or was also a continuation.
            
            # Exception: Empty lines or just whitespace are handled above.
            
            # We will append a "\n" to lines that seem to be inside a string.
            # How do we know?
            # It's safer to try to parse standard first, and only use this aggressive fixer if standard fails.
            # But here we are inside _fix_json which is called before parsing (or maybe we should call if after failure?)
            
            # Let's simple check the last char.
            last_char = stripped[-1]
            if last_char not in {',', '{', '[', '}', ']', '"', 'e', 'l', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}:
                # Likely inside a string.
                # E.g. "code": "def foo():
                # We want: "code": "def foo():\n
                fixed_lines.append(line + "\\n")
            else:
                fixed_lines.append(line)
                
        joined_json = "\n".join(fixed_lines)
        
        # 3. Aggressive missing key extraction for 'approved' (often buried inside the 'review' string)
        # Matches literal: Approved: false" \n }
        # And converts to: Approved: false", \n "approved": false \n }
        extracted_json = re.sub(
            r'([Aa]pproved:\s*(true|false|True|False))\s*"\s*\}', 
            lambda m: f'{m.group(1)}",\n  "approved": {m.group(2).lower()}\n}}', 
            joined_json
        )
        
        return extracted_json

    def _parse_response(self, response: str) -> AgentOutput:
        """Parse LLM response into structured output."""
        if self.output_schema:
            try:
                json_str = self._extract_json(response)
                if json_str:
                    # Attempt to fix common errors
                    json_str = self._fix_json(json_str)
                    
                    import json
                    parsed_data = None
                    try:
                        # Attempt orjson first (fastest)
                        parsed_data = orjson.loads(json_str)
                    except Exception:
                        try:
                            # Fallback to standard json with strict=False to handle literal newlines/control chars
                            parsed_data = json.loads(json_str, strict=False)
                        except Exception as je:
                            # Last Resort: Try to escape newlines manually if it looks like a "Expecting , delimiter" error
                            try:
                                # Very naive escape: escape all newlines? No, that breaks the structure.
                                # Let's try to trust the strict=False. 
                                # If that failed, we really have a syntax error.
                                # Let's log it and fail specificially.
                                print(f"FAILED TO PARSE JSON FOR {self.name}: {str(je)}")
                                # print(f"JSON START: ...{json_str[:100]}...")
                                # print(f"JSON END: ...{json_str[-100:]}")
                                return AgentOutput(success=False, errors=[f"JSON Parsing Error: {str(je)}"])
                            except Exception:
                                pass
                            return AgentOutput(success=False, errors=[f"JSON Parsing Error: {str(je)}"])
                    
                        # Pre-validation fix: LLMs sometimes omit 'approved' or output it as string
                        if isinstance(parsed_data, dict):
                            # Try to fix string booleans
                            for k, v in list(parsed_data.items()):
                                if isinstance(v, str):
                                    if v.lower() == "true":
                                        parsed_data[k] = True
                                    elif v.lower() == "false":
                                        parsed_data[k] = False
                                        
                            # Try to infer 'approved' if missing
                            if "review" in parsed_data and "approved" not in parsed_data:
                                review_text = parsed_data["review"].lower()
                                if "approved: false" in review_text or "not approved" in review_text or "not yet approved" in review_text:
                                    parsed_data["approved"] = False
                                elif "approved: true" in review_text or "is approved" in review_text:
                                    parsed_data["approved"] = True
                                else:
                                     # Default fallback to False to be safe
                                     parsed_data["approved"] = False

                        # Validate with Pydantic
                        data = self.output_schema.model_validate(parsed_data)
                        
                        return AgentOutput(
                            success=True,
                            artifacts=data.model_dump(),
                            message="Structured output generated"
                        )
                    except Exception as ve:
                        # Log the failure for debugging
                        print(f"VALIDATION FAILED FOR {self.name}: {str(ve)}")
                        return AgentOutput(success=False, errors=[f"Validation Error: {str(ve)}"])
                else:
                    return AgentOutput(success=False, errors=["No JSON found in response"])
            except Exception as e:
                return AgentOutput(success=False, errors=[f"Parsing Exception: {str(e)}"])
        else:
            return AgentOutput(success=True, message=response)

    def invoke(self, input_data: dict[str, Any], on_token: Optional[Callable[[str], None]] = None) -> AgentOutput:
        """
        Invoke the agent with input data.
        """
        try:
            # Build messages
            messages = [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": self._build_user_prompt(input_data)},
            ]
            
            # Invoke LLM
            response, usage = stream_llm(self.llm, messages, on_token=on_token)
            
            # Parse response
            output = self._parse_response(response)
            output.token_usage = usage
            
            return output
            
        except Exception as e:
            return AgentOutput(
                success=False,
                message=str(e),
                errors=[str(e)]
            )
