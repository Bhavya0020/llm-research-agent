import json
import asyncio
from typing import Dict, Any, List
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import JsonOutputParser

from .state import AgentState
from .prompts import GENERATE_QUERIES_PROMPT, REFLECT_PROMPT, SYNTHESIZE_PROMPT
from .tools import search_multiple_queries


def generate_queries(state: AgentState, llm: BaseChatModel) -> AgentState:
    """Generate search queries from the original question."""
    try:
        # Create prompt
        prompt = GENERATE_QUERIES_PROMPT.format(question=state.question)
        
        # Get LLM response
        response = llm.invoke([HumanMessage(content=prompt)])
        
        # Parse JSON response
        try:
            # Clean the response content - remove markdown code blocks if present
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]   # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove ```
            content = content.strip()
            
            queries = json.loads(content)
            if isinstance(queries, list):
                state.queries = queries[:5]  # Limit to 5 queries
            else:
                state.queries = [state.question]  # Fallback
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            state.queries = [state.question]
            
    except Exception as e:
        print(f"Error generating queries: {e}")
        state.queries = [state.question]  # Fallback
    
    return state


async def web_search_tool(state: AgentState) -> AgentState:
    """Search the web for all queries and merge results."""
    try:
        if not state.queries:
            return state
            
        # Search all queries concurrently
        docs = await search_multiple_queries(state.queries)
        state.docs = docs
        
    except Exception as e:
        print(f"Error in web search: {e}")
        state.docs = []
    
    return state


def reflect(state: AgentState, llm: BaseChatModel) -> AgentState:
    """Reflect on current results and decide if more search is needed using comprehensive slot-aware approach."""
    try:
        # Format docs for prompt with better structure
        docs_text = ""
        for i, doc in enumerate(state.docs, 1):
            docs_text += f"DOCUMENT {i}:\n"
            docs_text += f"Title: {doc.get('title', 'No title')}\n"
            docs_text += f"Content: {doc.get('snippet', 'No snippet')}\n"
            docs_text += f"URL: {doc.get('url', 'No URL')}\n\n"
        
        if not docs_text:
            docs_text = "No search results found."
        
        # Create prompt
        prompt = REFLECT_PROMPT.format(
            question=state.question,
            docs=docs_text
        )
        
        # Get LLM response
        response = llm.invoke([HumanMessage(content=prompt)])
        
        # Parse JSON response
        try:
            # Clean the response content - remove markdown code blocks if present
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]   # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove ```
            content = content.strip()
            
            reflection = json.loads(content)
            state.slots = reflection.get("slots", [])
            state.filled_slots = reflection.get("filled", [])
            state.need_more = reflection.get("need_more", False)
            state.new_queries = reflection.get("new_queries", [])
            
            # Enhanced slot validation logic
            if state.slots:
                # Validate that filled_slots are actually in the declared slots
                invalid_filled = set(state.filled_slots) - set(state.slots)
                if invalid_filled:
                    print(f"Warning: Invalid filled slots detected: {invalid_filled}")
                    state.filled_slots = [slot for slot in state.filled_slots if slot in state.slots]
                
                # Check if all mandatory slots are filled
                missing_slots = set(state.slots) - set(state.filled_slots)
                
                if missing_slots:
                    # We have missing slots, so we definitely need more
                    state.need_more = True
                    print(f"Missing slots: {missing_slots}")
                    
                    # Generate targeted queries for missing slots if none provided
                    if not state.new_queries:
                        state.new_queries = []
                        for slot in missing_slots:
                            # Create specific queries based on slot type
                            if slot in ["winner", "loser", "participants"]:
                                query = f"{slot} {state.question}"
                            elif slot in ["score", "result", "outcome"]:
                                query = f"final score result {state.question}"
                            elif slot in ["date", "when", "time"]:
                                query = f"date when {state.question}"
                            elif slot in ["location", "where", "venue"]:
                                query = f"location venue {state.question}"
                            else:
                                query = f"{slot} {state.question}"
                            state.new_queries.append(query)
                        state.new_queries = state.new_queries[:3]  # Limit to 3 queries
                else:
                    # All slots are filled, but double-check need_more flag
                    if not state.need_more:
                        print(f"All slots filled: {state.filled_slots}")
                    else:
                        # LLM says need_more but all slots are filled - this might be due to quality concerns
                        print(f"LLM indicates need_more despite all slots being filled. Quality check needed.")
            else:
                # No slots identified, fall back to simple logic
                if len(state.docs) < 2:
                    state.need_more = True
                    state.new_queries = [state.question]  # Try the original question again
                        
        except json.JSONDecodeError as e:
            print(f"JSON parsing error in reflect: {e}")
            print(f"Raw response: {response.content}")
            print(f"Cleaned content: {content}")
            # Fallback: assume we need more if we have few results
            state.need_more = len(state.docs) < 3
            state.new_queries = []
            state.slots = []
            state.filled_slots = []
            
    except Exception as e:
        print(f"Error in reflect: {e}")
        import traceback
        traceback.print_exc()
        state.need_more = len(state.docs) < 3
        state.new_queries = []
        state.slots = []
        state.filled_slots = []
    
    return state


def synthesize(state: AgentState, llm: BaseChatModel) -> AgentState:
    """Synthesize final answer from search results."""
    try:
        # Format docs for prompt
        docs_text = ""
        for i, doc in enumerate(state.docs, 1):
            docs_text += f"{i}. {doc.get('title', 'No title')}\n"
            docs_text += f"   {doc.get('snippet', 'No snippet')}\n"
            docs_text += f"   URL: {doc.get('url', 'No URL')}\n\n"
        
        if not docs_text:
            docs_text = "No search results found."
        
        # Create prompt with slots
        prompt = SYNTHESIZE_PROMPT.format(
            question=state.question,
            slots=state.slots,
            filled_slots=state.filled_slots,
            docs=docs_text
        )
        
        # Get LLM response
        response = llm.invoke([HumanMessage(content=prompt)])
        
        # Parse JSON response
        try:
            # Clean the response content - remove markdown code blocks if present
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]   # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove ```
            content = content.strip()
            
            synthesis = json.loads(content)
            state.answer = synthesis.get("answer", "Unable to generate answer.")
            citations = synthesis.get("citations", [])
            
            # Handle both old string format and new structured format
            if citations and isinstance(citations[0], dict):
                # New structured format
                state.citations = citations
            else:
                # Convert old string format to structured format
                structured_citations = []
                for i, citation in enumerate(citations, 1):
                    # Try to find matching doc by title
                    matching_doc = None
                    for doc in state.docs:
                        if doc.get('title', '').lower() in citation.lower() or citation.lower() in doc.get('title', '').lower():
                            matching_doc = doc
                            break
                    
                    if matching_doc:
                        structured_citations.append({
                            "id": i,
                            "title": matching_doc.get('title', citation),
                            "url": matching_doc.get('url', '')
                        })
                    else:
                        structured_citations.append({
                            "id": i,
                            "title": citation,
                            "url": ""
                        })
                state.citations = structured_citations
                
        except json.JSONDecodeError:
            # Fallback: create simple answer with structured citations
            if state.docs:
                state.answer = f"Based on the search results, here's what I found: {state.docs[0].get('snippet', 'No information available.')} [1]"
                state.citations = [{
                    "id": 1,
                    "title": state.docs[0].get('title', 'Unknown source'),
                    "url": state.docs[0].get('url', '')
                }]
            else:
                state.answer = "No information found"
                state.citations = []
                
    except Exception as e:
        print(f"Error in synthesize: {e}")
        import traceback
        traceback.print_exc()
        state.answer = "Error generating answer."
        state.citations = []
    
    return state


def should_continue(state: AgentState) -> str:
    """Determine if we should continue to another iteration using strict slot validation."""
    
    # If no slots are identified, use simple logic
    if not state.slots:
        if state.need_more and state.new_queries and state.iteration < state.max_iterations:
            return "continue"
        return "synthesize"
    
    # Check if all mandatory slots are filled
    missing_slots = set(state.slots) - set(state.filled_slots)
    slots_complete = len(missing_slots) == 0
    
    print(f"Slot analysis: {len(state.slots)} total slots, {len(state.filled_slots)} filled, {len(missing_slots)} missing")
    print(f"Missing slots: {missing_slots}")
    
    # STRICT RULE: If any mandatory slots are missing, continue searching
    if not slots_complete:
        if state.new_queries:
            print(f"Continuing search to fill missing slots: {missing_slots}")
            return "continue"
        else:
            print("No new queries available but slots are missing. Synthesizing with incomplete information.")
            return "synthesize"
    
    # All slots are filled - check if we should continue for quality reasons
    if state.need_more and state.new_queries and state.iteration < state.max_iterations:
        print("All slots filled but LLM indicates need for more information. Continuing for quality.")
        return "continue"
    
    # All slots filled and no need for more, or max iterations reached
    print("All slots filled and ready to synthesize.")
    return "synthesize"


def update_iteration(state: AgentState) -> AgentState:
    """Update iteration count and prepare for next round."""
    state.iteration += 1
    if state.need_more and state.new_queries:
        state.queries = state.new_queries
        state.docs = []  # Clear previous results
        state.need_more = False
        state.new_queries = []
        # Keep slots but clear filled_slots for next iteration
        state.filled_slots = []
    
    return state 