import asyncio
from typing import Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, END
import uuid

from .state import AgentState
from .nodes import (
    generate_queries, 
    web_search_tool, 
    reflect, 
    synthesize, 
    should_continue, 
    update_iteration
)


def create_agent_graph(llm: BaseChatModel) -> StateGraph:
    """Create the LangGraph pipeline for the research agent."""
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("generate_queries", lambda state: generate_queries(state, llm))
    workflow.add_node("web_search", lambda state: asyncio.run(web_search_tool(state)))
    workflow.add_node("reflect", lambda state: reflect(state, llm))
    workflow.add_node("synthesize", lambda state: synthesize(state, llm))
    workflow.add_node("update_iteration", update_iteration)
    
    # Set entry point
    workflow.set_entry_point("generate_queries")
    
    # Add edges
    workflow.add_edge("generate_queries", "web_search")
    workflow.add_edge("web_search", "reflect")
    workflow.add_conditional_edges(
        "reflect",
        should_continue,
        {
            "continue": "update_iteration",
            "synthesize": "synthesize"
        }
    )
    workflow.add_edge("update_iteration", "web_search")
    workflow.add_edge("synthesize", END)
    
    return workflow


async def run_agent(question: str, llm: BaseChatModel, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """Run the research agent on a question."""
    graph = create_agent_graph(llm)
    app = graph.compile()  # No checkpointer for langgraph 0.5.0
    initial_state = AgentState(question=question)
    try:
        result = await app.ainvoke(initial_state)  # No additional arguments
        docs = result.get("docs", [])
        mock_results = any(doc.get("mock") for doc in docs)
        # In langgraph 0.5.0, the result is a dict with state attributes as keys
        if isinstance(result, dict):
            return {
                "answer": result.get("answer", ""),
                "citations": result.get("citations", []),
                "slots": result.get("slots", []),
                "filled_slots": result.get("filled_slots", []),
                "iterations": result.get("iteration", 0)
            }
        else:
            # Fallback for unexpected result type
            return {
                "answer": "Unexpected result format",
                "citations": [],
                "slots": [],
                "filled_slots": [],
                "iterations": 0
            }
    except Exception as e:
        print(f"Error running agent: {e}")
        return {
            "answer": "Error occurred while processing the question.",
            "citations": [],
            "slots": [],
            "filled_slots": [],
            "iterations": 0
        }


def run_agent_sync(question: str, llm: BaseChatModel, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """Synchronous wrapper for run_agent."""
    return asyncio.run(run_agent(question, llm, thread_id=thread_id)) 