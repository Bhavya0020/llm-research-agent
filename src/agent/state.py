from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from langchain_core.messages import BaseMessage


@dataclass
class AgentState:
    """State for the LLM research agent pipeline."""
    
    # Input
    question: str
    
    # Generated queries
    queries: List[str] = field(default_factory=list)
    
    # Search results
    docs: List[Dict[str, Any]] = field(default_factory=list)
    
    # Reflection state (Slot-Aware)
    need_more: bool = False
    new_queries: List[str] = field(default_factory=list)
    slots: List[str] = field(default_factory=list)
    filled_slots: List[str] = field(default_factory=list)
    
    # Final output
    answer: str = ""
    citations: List[str] = field(default_factory=list)
    
    # Iteration tracking
    iteration: int = 0
    max_iterations: int = 2
    
    # Messages for LLM context
    messages: List[BaseMessage] = field(default_factory=list) 