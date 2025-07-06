#!/usr/bin/env python3
"""
Research Agent Node Graph Visualizer

This script creates a visual representation of the research agent's node graph structure.
"""

def print_text_graph():
    """Print a text-based representation of the agent's node graph."""
    
    graph = """
    RESEARCH AGENT NODE GRAPH STRUCTURE
    ===================================
    
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
    
    NODE TYPES:
    ───────────
    🔴 LLM Nodes: generate_queries, reflect, synthesize
    🔵 Tool Nodes: web_search
    🟢 Logic Nodes: update_iteration, should_continue
    🟡 Output Nodes: END
    
    DATA FLOW:
    ──────────
    State → generate_queries → web_search → reflect → [decision] → synthesize → END
                                    ↓
                              update_iteration → web_search (loop)
    
    SLOT-AWARE LOGIC:
    ─────────────────
    1. reflect identifies mandatory slots based on question type
    2. Matches evidence from search results to specific slots
    3. Only marks slots as "filled" with clear, consistent evidence
    4. Generates targeted queries for missing slots
    5. Continues until ALL slots are filled or max iterations reached
    
    DECISION LOGIC:
    ───────────────
    should_continue() function determines next step:
    • If missing slots AND have new_queries → continue
    • If all slots filled AND need_more=false → synthesize
    • If max iterations reached → synthesize
    • If no new queries but missing slots → synthesize (incomplete)
    
    ERROR HANDLING:
    ───────────────
    • JSON parsing errors → fallback to reasonable defaults
    • API failures → graceful degradation
    • Rate limits → proper error handling
    • Timeouts → configurable limits with fallbacks
    """
    
    return graph

def print_node_details():
    """Print detailed information about each node."""
    
    details = """
    DETAILED NODE INFORMATION
    =========================
    
    🔴 generate_queries (LLM Node)
    ─────────────────────────────
    Purpose: Break down the original question into specific search queries
    Input: AgentState with question
    Output: AgentState with queries array
    Process:
      • Format question using GENERATE_QUERIES_PROMPT
      • Invoke LLM with structured prompt
      • Parse JSON response containing query array
      • Fallback to original question if parsing fails
    Error Handling: JSON parsing errors → use original question
    
    🔵 web_search (Tool Node)
    ─────────────────────────
    Purpose: Execute concurrent web searches and merge results
    Input: AgentState with queries
    Output: AgentState with docs array
    Process:
      • Check if queries exist in state
      • Execute all queries concurrently using asyncio.gather()
      • Merge results and deduplicate by URL
      • Handle individual query failures gracefully
    Performance: Concurrent execution reduces total search time
    Fallback: Mock search tool for offline development
    
    🔴 reflect (LLM Node - Slot-Aware)
    ──────────────────────────────────
    Purpose: Evaluate search results using comprehensive slot-based approach
    Input: AgentState with docs
    Output: AgentState with slots, filled_slots, need_more, new_queries
    Process:
      • Format search results for LLM consumption
      • Identify mandatory information slots based on question type
      • Match evidence sentences to specific slots
      • Judge completeness and consistency
      • Generate targeted queries for missing slots
    Slot Types:
      • WHO: winner, opponent, participants, key_people
      • WHAT: definition, features, characteristics
      • WHEN: date, time_period, duration
      • WHERE: location, venue, place
      • HOW: method, process, steps
    Validation: Only mark slots as "filled" with clear, consistent evidence
    
    🟢 update_iteration (Logic Node)
    ───────────────────────────────
    Purpose: Update iteration count and prepare for next round
    Input: AgentState
    Output: AgentState with updated iteration and new queries
    Process:
      • Increment iteration counter
      • Set new queries for next round if available
      • Clear previous results but keep slots
      • Reset filled_slots for next iteration
    Logic: Prepares state for continued search with refined queries
    
    🟢 should_continue (Logic Node)
    ──────────────────────────────
    Purpose: Determine if we should continue to another iteration
    Input: AgentState
    Output: String ("continue" or "synthesize")
    Decision Logic:
      • If no slots identified → use simple logic based on need_more
      • If missing slots AND have new_queries → continue
      • If all slots filled AND need_more=false → synthesize
      • If max iterations reached → synthesize
      • If all slots filled but need_more=true → continue for quality
    Strict Rule: Missing mandatory slots trigger continuation
    
    🔴 synthesize (LLM Node)
    ────────────────────────
    Purpose: Create final concise answer with structured citations
    Input: AgentState with docs, slots, filled_slots
    Output: AgentState with answer and citations
    Process:
      • Format all search results for LLM
      • Generate direct, concise answer (≤80 words)
      • Create structured citations with id, title, url
      • Handle both old and new citation formats
    Quality Constraints:
      • Maximum 80 words (≈400 characters)
      • Must include Markdown citations [1][2]...
      • Direct answers without filler phrases
      • Structured citations with metadata
    
    🟡 END (Output Node)
    ───────────────────
    Purpose: Return final result in clean JSON format
    Input: AgentState
    Output: JSON response
    Format:
      {
        "answer": "Direct, concise answer with citations",
        "citations": [{"id": 1, "title": "...", "url": "..."}],
        "slots": ["slot1", "slot2", "slot3"],
        "filled_slots": ["slot1", "slot2"],
        "iterations": N
      }
    """
    
    return details

def print_flow_examples():
    """Print example flows through the graph."""
    
    examples = """
    EXAMPLE FLOWS THROUGH THE GRAPH
    ===============================
    
    🎯 Example 1: Simple Question (1 iteration)
    ───────────────────────────────────────────
    Question: "What is Python?"
    
    Flow:
    1. generate_queries → ["python programming", "python language", "python features"]
    2. web_search → 3 search results
    3. reflect → slots: ["definition", "features"], filled: ["definition", "features"], need_more: false
    4. should_continue → "synthesize" (all slots filled)
    5. synthesize → "Python is a high-level, interpreted programming language..."
    6. END → JSON response
    
    🎯 Example 2: Complex Question (Multiple iterations)
    ───────────────────────────────────────────────────
    Question: "Who won the 2022 FIFA World Cup?"
    
    Flow:
    Iteration 1:
    1. generate_queries → ["2022 FIFA World Cup winner", "World Cup 2022 final"]
    2. web_search → 2 search results
    3. reflect → slots: ["winner", "opponent", "score", "date", "venue"], 
                filled: ["winner"], need_more: true
    4. should_continue → "continue" (missing slots)
    5. update_iteration → iteration=1, new_queries=["France Argentina 2022 final score", "World Cup 2022 date"]
    
    Iteration 2:
    6. web_search → 2 more search results
    7. reflect → slots: ["winner", "opponent", "score", "date", "venue"],
                filled: ["winner", "opponent", "score"], need_more: true
    8. should_continue → "continue" (still missing slots)
    9. update_iteration → iteration=2, new_queries=["2022 World Cup final venue"]
    
    Iteration 3:
    10. web_search → 1 more search result
    11. reflect → slots: ["winner", "opponent", "score", "date", "venue"],
                 filled: ["winner", "opponent", "score", "date", "venue"], need_more: false
    12. should_continue → "synthesize" (all slots filled)
    13. synthesize → "Argentina won the 2022 FIFA World Cup, beating France..."
    14. END → Complete JSON response
    
    🎯 Example 3: Error Handling
    ────────────────────────────
    Question: "What is XYZ?" (unknown topic)
    
    Flow:
    1. generate_queries → ["XYZ", "what is XYZ"]
    2. web_search → 0 search results (API error or no results)
    3. reflect → slots: [], filled: [], need_more: true (fallback logic)
    4. should_continue → "continue" (need_more=true)
    5. update_iteration → iteration=1, new_queries=["XYZ"]
    6. web_search → 0 search results again
    7. reflect → slots: [], filled: [], need_more: false (max iterations)
    8. should_continue → "synthesize"
    9. synthesize → "No relevant information found to answer the question."
    10. END → Error response
    
    SLOT VALIDATION EXAMPLES:
    ─────────────────────────
    
    ✅ Valid Slot Filling:
    Question: "Who won the 2022 World Cup?"
    Slots: ["winner", "opponent", "score", "date"]
    Evidence: "Argentina won the 2022 World Cup, beating France 4-2 on penalties"
    Filled: ["winner", "opponent", "score"] (clear evidence)
    Missing: ["date"] → continue searching
    
    ❌ Invalid Slot Filling:
    Question: "Who won the 2022 World Cup?"
    Slots: ["winner", "opponent", "score", "date"]
    Evidence: "Argentina won the World Cup" (vague, no opponent/score/date)
    Filled: ["winner"] (only clear evidence)
    Missing: ["opponent", "score", "date"] → continue searching
    
    🔄 Iteration Logic:
    ──────────────────
    • Max iterations: 2 (configurable)
    • Slot completion takes priority over iteration limits
    • Quality concerns can trigger additional iterations even with filled slots
    • Missing slots always trigger continuation (if new queries available)
    """
    
    return examples

if __name__ == "__main__":
    print("=" * 80)
    print(print_text_graph())
    print("=" * 80)
    print(print_node_details())
    print("=" * 80)
    print(print_flow_examples())
    print("=" * 80) 