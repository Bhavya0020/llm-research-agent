#!/usr/bin/env python3
"""
LangGraph Visualization using get_graph() method

This script creates a visual representation of the research agent's LangGraph structure
using the built-in get_graph() method for accurate graph representation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from langchain_openai import ChatOpenAI
from agent.graph import create_agent_graph
from agent.llm_factory import get_llm

def create_langgraph_visualization():
    """Create a visualization of the LangGraph structure using get_graph()."""
    
    print("Creating LangGraph visualization using get_graph() method...")
    
    # Create the LLM (we'll use a mock one for visualization)
    try:
        llm = get_llm()
    except:
        # Fallback to a mock LLM if API keys aren't set
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    # Create the agent graph
    workflow = create_agent_graph(llm)
    
    # Get the graph structure
    graph = workflow.get_graph()
    
    print("\n" + "="*80)
    print("LANGGRAPH RESEARCH AGENT STRUCTURE")
    print("="*80)
    
    # Print graph information
    print(f"\nGraph Type: {type(graph).__name__}")
    print(f"Number of nodes: {len(graph.nodes)}")
    print(f"Number of edges: {len(graph.edges)}")
    
    # Print nodes
    print("\n" + "-"*50)
    print("NODES:")
    print("-"*50)
    for node_id, node_data in graph.nodes.items():
        print(f"Node ID: {node_id}")
        print(f"  Type: {type(node_data).__name__}")
        if hasattr(node_data, 'name'):
            print(f"  Name: {node_data.name}")
        if hasattr(node_data, 'description'):
            print(f"  Description: {node_data.description}")
        print()
    
    # Print edges
    print("-"*50)
    print("EDGES:")
    print("-"*50)
    for edge in graph.edges:
        print(f"From: {edge.source}")
        print(f"To: {edge.target}")
        if hasattr(edge, 'label'):
            print(f"Label: {edge.label}")
        print()
    
    # Print conditional edges
    print("-"*50)
    print("CONDITIONAL EDGES:")
    print("-"*50)
    for node_id, node_data in graph.nodes.items():
        if hasattr(node_data, 'conditional_edges'):
            print(f"Node: {node_id}")
            for condition, target in node_data.conditional_edges.items():
                print(f"  Condition: {condition} -> Target: {target}")
            print()
    
    # Create a text-based graph representation
    print("-"*50)
    print("TEXT-BASED GRAPH REPRESENTATION:")
    print("-"*50)
    
    # Build adjacency list
    adjacency = {}
    for edge in graph.edges:
        if edge.source not in adjacency:
            adjacency[edge.source] = []
        adjacency[edge.source].append(edge.target)
    
    # Add conditional edges
    for node_id, node_data in graph.nodes.items():
        if hasattr(node_data, 'conditional_edges'):
            if node_id not in adjacency:
                adjacency[node_id] = []
            for condition, target in node_data.conditional_edges.items():
                adjacency[node_id].append(f"{target} ({condition})")
    
    # Print the graph structure
    for node_id in sorted(adjacency.keys()):
        print(f"{node_id}:")
        for target in adjacency[node_id]:
            print(f"  -> {target}")
        print()
    
    # Create a more detailed analysis
    print("-"*50)
    print("DETAILED ANALYSIS:")
    print("-"*50)
    
    # Analyze node types
    llm_nodes = []
    tool_nodes = []
    logic_nodes = []
    decision_nodes = []
    
    for node_id, node_data in graph.nodes.items():
        if 'generate_queries' in node_id or 'reflect' in node_id or 'synthesize' in node_id:
            llm_nodes.append(node_id)
        elif 'web_search' in node_id:
            tool_nodes.append(node_id)
        elif 'update_iteration' in node_id:
            logic_nodes.append(node_id)
        elif hasattr(node_data, 'conditional_edges'):
            decision_nodes.append(node_id)
    
    print(f"LLM Nodes ({len(llm_nodes)}): {', '.join(llm_nodes)}")
    print(f"Tool Nodes ({len(tool_nodes)}): {', '.join(tool_nodes)}")
    print(f"Logic Nodes ({len(logic_nodes)}): {', '.join(logic_nodes)}")
    print(f"Decision Nodes ({len(decision_nodes)}): {', '.join(decision_nodes)}")
    
    # Analyze the flow
    print("\nFLOW ANALYSIS:")
    print("1. Entry Point: generate_queries")
    print("2. Sequential Flow: generate_queries -> web_search -> reflect")
    print("3. Decision Point: reflect -> should_continue function")
    print("4. Conditional Flow:")
    print("   - continue -> update_iteration -> web_search (loop)")
    print("   - synthesize -> END")
    print("5. Exit Point: synthesize -> END")
    
    # Create a visual ASCII representation
    print("\n" + "-"*50)
    print("ASCII GRAPH REPRESENTATION:")
    print("-"*50)
    
    ascii_graph = """
    START
      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │                    generate_queries (LLM)                      │
    │  • Break question into 3-5 specific search queries             │
    │  • Return JSON array of queries                                │
    │  • Fallback to original question if parsing fails              │
    └─────────────────────────────────────────────────────────────────┘
      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │                    web_search (Tool)                           │
    │  • Execute concurrent searches using Google Custom Search API  │
    │  • Merge and deduplicate results by URL                        │
    │  • Fallback to mock search if API keys not set                 │
    │  • Handle rate limits and timeouts gracefully                  │
    └─────────────────────────────────────────────────────────────────┘
      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │                  reflect (LLM - Slot-Aware)                   │
    │  • Identify mandatory information slots                        │
    │  • Match evidence sentences to specific slots                  │
    │  • Judge completeness and consistency                          │
    │  • Generate targeted queries for missing slots                 │
    │  • Return: {slots, filled, need_more, new_queries}            │
    └─────────────────────────────────────────────────────────────────┘
      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │                    DECISION POINT                              │
    │                    should_continue()                           │
    │                                                                 │
    │  ┌─────────────────┐                    ┌─────────────────┐    │
    │  │   continue      │                    │   synthesize    │    │
    │  │   (if missing   │                    │   (if all slots │    │
    │  │    slots or     │                    │    filled or    │    │
    │  │    need more)   │                    │   max iter)     │    │
    │  └─────────────────┘                    └─────────────────┘    │
    │          ↓                              └─────────────────┘    │
    │  ┌─────────────────────────────────────────────────────────┐    │
    │  │              update_iteration (Logic)                   │    │
    │  │  • Increment iteration counter                          │    │
    │  │  • Set new queries for next round                       │    │
    │  │  • Clear previous results, keep slots                   │    │
    │  │  • Reset filled_slots for next iteration                │    │
    │  └─────────────────────────────────────────────────────────┘    │
    │          ↓                                                      │
    │  ┌─────────────────────────────────────────────────────────┐    │
    │  │                    web_search                           │    │
    │  │                    (loop back)                          │    │
    │  └─────────────────────────────────────────────────────────┘    │
    └─────────────────────────────────────────────────────────────────┘
      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │                   synthesize (LLM)                            │
    │  • Generate concise answer (≤80 words)                        │
    │  • Create structured citations with id, title, url            │
    │  • Handle both old and new citation formats                   │
    │  • Return clean JSON format                                   │
    └─────────────────────────────────────────────────────────────────┘
      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │                        END                                    │
    │  • Return: {"answer": "...", "citations": [...],              │
    │            "slots": [...], "filled_slots": [...],             │
    │            "iterations": N}                                   │
    └─────────────────────────────────────────────────────────────────┘
    """
    
    print(ascii_graph)
    
    # Create a JSON representation of the graph
    print("\n" + "-"*50)
    print("JSON GRAPH REPRESENTATION:")
    print("-"*50)
    
    graph_json = {
        "graph_type": "StateGraph",
        "nodes": {},
        "edges": [],
        "conditional_edges": {}
    }
    
    # Add nodes
    for node_id, node_data in graph.nodes.items():
        graph_json["nodes"][node_id] = {
            "type": type(node_data).__name__,
            "has_conditional_edges": hasattr(node_data, 'conditional_edges')
        }
    
    # Add edges
    for edge in graph.edges:
        graph_json["edges"].append({
            "source": edge.source,
            "target": edge.target
        })
    
    # Add conditional edges
    for node_id, node_data in graph.nodes.items():
        if hasattr(node_data, 'conditional_edges'):
            graph_json["conditional_edges"][node_id] = node_data.conditional_edges
    
    import json
    print(json.dumps(graph_json, indent=2))
    
    return graph

def create_graph_statistics(graph):
    """Create statistics about the graph structure."""
    
    print("\n" + "="*80)
    print("GRAPH STATISTICS")
    print("="*80)
    
    # Count node types
    node_types = {}
    for node_id, node_data in graph.nodes.items():
        node_type = type(node_data).__name__
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    print(f"\nNode Type Distribution:")
    for node_type, count in node_types.items():
        print(f"  {node_type}: {count}")
    
    # Count edge types
    edge_count = len(graph.edges)
    conditional_edge_count = sum(
        1 for node_data in graph.nodes.values() 
        if hasattr(node_data, 'conditional_edges')
    )
    
    print(f"\nEdge Statistics:")
    print(f"  Regular edges: {edge_count}")
    print(f"  Conditional edges: {conditional_edge_count}")
    print(f"  Total edges: {edge_count + conditional_edge_count}")
    
    # Find entry and exit points
    entry_points = []
    exit_points = []
    
    # Check for nodes with no incoming edges (entry points)
    incoming_edges = {}
    for edge in graph.edges:
        if edge.target not in incoming_edges:
            incoming_edges[edge.target] = 0
        incoming_edges[edge.target] += 1
    
    for node_id in graph.nodes:
        if node_id not in incoming_edges:
            entry_points.append(node_id)
    
    # Check for nodes with no outgoing edges (exit points)
    outgoing_edges = {}
    for edge in graph.edges:
        if edge.source not in outgoing_edges:
            outgoing_edges[edge.source] = 0
        outgoing_edges[edge.source] += 1
    
    for node_id in graph.nodes:
        if node_id not in outgoing_edges:
            exit_points.append(node_id)
    
    print(f"\nEntry Points: {entry_points}")
    print(f"Exit Points: {exit_points}")
    
    # Calculate graph complexity
    total_nodes = len(graph.nodes)
    total_edges = edge_count + conditional_edge_count
    complexity = total_edges / total_nodes if total_nodes > 0 else 0
    
    print(f"\nGraph Complexity:")
    print(f"  Total nodes: {total_nodes}")
    print(f"  Total edges: {total_edges}")
    print(f"  Edge-to-node ratio: {complexity:.2f}")

def main():
    """Main function to create the LangGraph visualization."""
    
    try:
        # Create the graph visualization
        graph = create_langgraph_visualization()
        
        # Create graph statistics
        create_graph_statistics(graph)
        
        print("\n" + "="*80)
        print("VISUALIZATION COMPLETE")
        print("="*80)
        print("\nThe LangGraph structure has been analyzed and displayed above.")
        print("This shows the actual graph structure as defined in your code.")
        print("\nKey features of your research agent:")
        print("• Slot-aware reflection for comprehensive information gathering")
        print("• Iterative search refinement based on missing information")
        print("• Conditional flow control for optimal search completion")
        print("• Structured output with citations and metadata")
        
    except Exception as e:
        print(f"Error creating visualization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 