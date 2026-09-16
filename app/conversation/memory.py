"""
Simple in-memory conversation memory.
Stores message history keyed by conversation_id.
"""
from typing import Dict, List
from collections import defaultdict


_history: Dict[str, List[Dict[str, str]]] = defaultdict(list)
MAX_MESSAGES = 12


def add_to_history(conversation_id: str, role: str, content: str):
    """Append a message to conversation history."""
    _history[conversation_id].append({"role": role, "content": content})
    # Trim to last MAX_MESSAGES
    if len(_history[conversation_id]) > MAX_MESSAGES:
        _history[conversation_id] = _history[conversation_id][-MAX_MESSAGES:]


def get_conversation_history(conversation_id: str) -> str:
    """Return formatted history as a string for the LLM."""
    messages = _history.get(conversation_id, [])
    if not messages:
        return "No previous conversation."

    lines = []
    for msg in messages:
        role = msg["role"].upper()
        content = msg["content"][:500]  # cap each message
        lines.append(f"{role}: {content}")

    return "\n".join(lines)


def clear_history(conversation_id: str):
    """Clear a conversation."""
    _history.pop(conversation_id, None)