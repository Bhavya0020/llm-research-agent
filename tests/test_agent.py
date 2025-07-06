import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from langchain_core.messages import AIMessage

from src.agent.state import AgentState
from src.agent.nodes import generate_queries, reflect, synthesize, should_continue
from src.agent.tools import MockWebSearchTool, GoogleCustomSearchTool
from src.agent.graph import run_agent_sync
from src.agent.llm_factory import get_llm


class TestAgentNodes:
    """Test individual agent nodes."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = Mock()
        self.state = AgentState(question="What is Python?")
    
    def test_generate_queries_happy_path(self):
        """Test happy path for query generation."""
        # Mock LLM response
        self.mock_llm.invoke.return_value = AIMessage(
            content='["python programming language", "python features", "python syntax"]'
        )
        
        result = generate_queries(self.state, self.mock_llm)
        
        assert len(result.queries) == 3
        assert "python programming language" in result.queries
        assert self.mock_llm.invoke.called
    
    def test_generate_queries_json_error(self):
        """Test query generation with JSON parsing error."""
        # Mock LLM response with invalid JSON
        self.mock_llm.invoke.return_value = AIMessage(content="Invalid JSON response")
        
        result = generate_queries(self.state, self.mock_llm)
        
        # Should fallback to original question
        assert result.queries == [self.state.question]
    
    def test_generate_queries_llm_error(self):
        """Test query generation with LLM error."""
        # Mock LLM error
        self.mock_llm.invoke.side_effect = Exception("LLM error")
        
        result = generate_queries(self.state, self.mock_llm)
        
        # Should fallback to original question
        assert result.queries == [self.state.question]
    
    def test_reflect_need_more(self):
        """Test reflect node when more search is needed."""
        # Add some docs to state
        self.state.docs = [
            {"title": "Doc 1", "snippet": "Some info", "url": "http://example.com"}
        ]
        
        # Mock LLM response indicating need for more search (no slots identified)
        self.mock_llm.invoke.return_value = AIMessage(
            content='{"need_more": true, "new_queries": ["more specific query"]}'
        )
        
        result = reflect(self.state, self.mock_llm)
        
        assert result.need_more is True
        # The function may generate fallback queries, so just check that we have some queries
        assert len(result.new_queries) >= 1
    
    def test_reflect_no_more_needed(self):
        """Test reflect node when no more search is needed."""
        # Add some docs to state
        self.state.docs = [
            {"title": "Doc 1", "snippet": "Good info", "url": "http://example.com"},
            {"title": "Doc 2", "snippet": "More good info", "url": "http://example2.com"}
        ]
        
        # Mock LLM response indicating no more search needed
        self.mock_llm.invoke.return_value = AIMessage(
            content='{"need_more": false, "new_queries": []}'
        )
        
        result = reflect(self.state, self.mock_llm)
        
        assert result.need_more is False
        assert len(result.new_queries) == 0
    
    def test_reflect_json_error(self):
        """Test reflect node with JSON parsing error."""
        # Add some docs to state
        self.state.docs = [{"title": "Doc 1", "snippet": "Info", "url": "http://example.com"}]
        
        # Mock LLM response with invalid JSON
        self.mock_llm.invoke.return_value = AIMessage(content="Invalid JSON")
        
        result = reflect(self.state, self.mock_llm)
        
        # Should fallback based on number of docs
        assert result.need_more is True  # Only 1 doc, so need more
        assert result.slots == []
        assert result.filled_slots == []
    
    def test_reflect_slot_aware_complete(self):
        """Test slot-aware reflect when all slots are filled."""
        # Add some docs to state
        self.state.docs = [
            {"title": "World Cup 2022", "snippet": "Argentina won the 2022 World Cup", "url": "http://example.com"},
            {"title": "Final Score", "snippet": "Argentina defeated France 4-2 on penalties", "url": "http://example2.com"}
        ]
        
        # Mock LLM response with complete slot information
        self.mock_llm.invoke.return_value = AIMessage(
            content='{"slots": ["winner", "opponent", "score", "date"], "filled": ["winner", "opponent", "score", "date"], "need_more": false, "new_queries": []}'
        )
        
        result = reflect(self.state, self.mock_llm)
        
        assert result.need_more is False
        assert result.slots == ["winner", "opponent", "score", "date"]
        assert result.filled_slots == ["winner", "opponent", "score", "date"]
        assert len(result.new_queries) == 0
        
        # Test that all declared slots are filled
        missing_slots = set(result.slots) - set(result.filled_slots)
        assert len(missing_slots) == 0, f"Missing slots: {missing_slots}"
    
    def test_reflect_slot_aware_incomplete(self):
        """Test slot-aware reflect when some slots are missing."""
        # Add some docs to state
        self.state.docs = [
            {"title": "World Cup 2022", "snippet": "Argentina won the 2022 World Cup", "url": "http://example.com"}
        ]
        
        # Mock LLM response with incomplete slot information
        self.mock_llm.invoke.return_value = AIMessage(
            content='{"slots": ["winner", "score", "date"], "filled": ["winner"], "need_more": true, "new_queries": ["Argentina France 2022 final score", "World Cup 2022 date"]}'
        )
        
        result = reflect(self.state, self.mock_llm)
        
        assert result.need_more is True
        assert result.slots == ["winner", "score", "date"]
        assert result.filled_slots == ["winner"]
        assert len(result.new_queries) == 2
        assert "score" in result.new_queries[0]
        assert "date" in result.new_queries[1]
    
    def test_reflect_slot_aware_validation(self):
        """Test slot-aware reflect validation logic."""
        # Add some docs to state
        self.state.docs = [
            {"title": "World Cup 2022", "snippet": "Argentina won", "url": "http://example.com"}
        ]
        
        # Mock LLM response with slots but no filled slots
        self.mock_llm.invoke.return_value = AIMessage(
            content='{"slots": ["winner", "score"], "filled": [], "need_more": false, "new_queries": []}'
        )
        
        result = reflect(self.state, self.mock_llm)
        
        # Validation should override and set need_more to True
        assert result.need_more is True
        assert result.slots == ["winner", "score"]
        assert result.filled_slots == []
    
    def test_reflect_slot_aware_missing_slots(self):
        """Test slot-aware reflect with missing slots detection."""
        # Add some docs to state
        self.state.docs = [
            {"title": "World Cup 2022", "snippet": "Argentina won", "url": "http://example.com"}
        ]
        
        # Mock LLM response with missing slots
        self.mock_llm.invoke.return_value = AIMessage(
            content='{"slots": ["winner", "score", "date"], "filled": ["winner"], "need_more": false, "new_queries": []}'
        )
        
        result = reflect(self.state, self.mock_llm)
        
        # Validation should detect missing slots and set need_more to True
        assert result.need_more is True
        assert result.slots == ["winner", "score", "date"]
        assert result.filled_slots == ["winner"]
        # Should generate targeted queries for missing slots
        assert len(result.new_queries) > 0
    
    def test_synthesize_happy_path(self):
        """Test synthesize node happy path."""
        # Add docs to state
        self.state.docs = [
            {"title": "Python Guide", "snippet": "Python is a programming language", "url": "http://python.org"}
        ]
        
        # Mock LLM response with structured citations
        self.mock_llm.invoke.return_value = AIMessage(
            content='{"answer": "Python is a programming language [1]", "citations": [{"id": 1, "title": "Python Guide", "url": "http://python.org"}]}'
        )
        
        result = synthesize(self.state, self.mock_llm)
        
        assert "Python is a programming language" in result.answer
        assert "[1]" in result.answer
        assert len(result.citations) == 1
        assert result.citations[0]["title"] == "Python Guide"
        assert result.citations[0]["id"] == 1
    
    def test_synthesize_no_docs(self):
        """Test synthesize node with no search results."""
        # Mock LLM response
        self.mock_llm.invoke.return_value = AIMessage(
            content='{"answer": "No information found", "citations": []}'
        )
        
        result = synthesize(self.state, self.mock_llm)
        
        assert "No information found" in result.answer
        assert len(result.citations) == 0
    
    def test_synthesize_json_error(self):
        """Test synthesize node with JSON parsing error."""
        # Add docs to state
        self.state.docs = [
            {"title": "Python Guide", "snippet": "Python is a programming language", "url": "http://python.org"}
        ]
        
        # Mock LLM response with invalid JSON
        self.mock_llm.invoke.return_value = AIMessage(content="Invalid JSON")
        
        result = synthesize(self.state, self.mock_llm)
        
        # Should create fallback answer
        assert "Based on the search results" in result.answer
        assert len(result.citations) == 1
    
    def test_should_continue_max_iterations(self):
        """Test should_continue when max iterations reached."""
        self.state.iteration = 2
        self.state.max_iterations = 2
        
        result = should_continue(self.state)
        
        assert result == "synthesize"
    
    def test_should_continue_need_more(self):
        """Test should_continue when more search is needed."""
        self.state.iteration = 0
        self.state.need_more = True
        self.state.new_queries = ["new query"]
        
        result = should_continue(self.state)
        
        assert result == "continue"
    
    def test_should_continue_no_more_needed(self):
        """Test should_continue when no more search is needed."""
        self.state.iteration = 0
        self.state.need_more = False
        self.state.new_queries = []
        
        result = should_continue(self.state)
        
        assert result == "synthesize"


class TestSearchTools:
    """Test search tools."""
    
    def test_mock_search_tool(self):
        """Test mock search tool."""
        tool = MockWebSearchTool()
        
        # Test with known query
        result = asyncio.run(tool._arun("python programming"))
        
        assert len(result) > 0
        assert "title" in result[0]
        assert "snippet" in result[0]
        assert "url" in result[0]
    
    def test_mock_search_tool_unknown_query(self):
        """Test mock search tool with unknown query."""
        tool = MockWebSearchTool()
        
        result = asyncio.run(tool._arun("unknown query"))
        
        assert len(result) == 1
        assert "unknown query" in result[0]["title"]
    
    @patch.dict('os.environ', {'GOOGLE_CSE_API_KEY': 'test_key', 'GOOGLE_CSE_CX': 'test_cx'})
    def test_google_custom_search_tool_initialization(self):
        """Test Google Custom Search tool initialization."""
        tool = GoogleCustomSearchTool()
        assert tool._endpoint == "https://www.googleapis.com/customsearch/v1"
        assert tool._api_key == 'test_key'
        assert tool._cx == 'test_cx'


class TestAgentIntegration:
    """Test agent integration."""
    
    @patch('src.agent.llm_factory.get_llm')
    def test_agent_happy_path(self, mock_get_llm):
        """Test happy path for the complete agent."""
        # Mock LLM
        mock_llm = Mock()
        mock_llm.invoke.side_effect = [
            AIMessage(content='["python programming", "python language"]'),  # generate_queries
            AIMessage(content='{"slots": ["definition", "features"], "filled": ["definition", "features"], "need_more": false, "new_queries": []}'),  # reflect
            AIMessage(content='{"answer": "Python is a language [1]", "citations": [{"id": 1, "title": "Python Guide", "url": "http://python.org"}]}')  # synthesize
        ]
        mock_get_llm.return_value = mock_llm
        
        # Mock search tool
        with patch('src.agent.tools.get_search_tool') as mock_get_tool:
            mock_tool = Mock()
            mock_tool._arun = AsyncMock(return_value=[
                {"title": "Python Guide", "snippet": "Python is a programming language", "url": "http://python.org"}
            ])
            mock_get_tool.return_value = mock_tool
            
            result = run_agent_sync("What is Python?", mock_llm, thread_id="test-thread-happy-path")
            
            assert "Python is a language" in result["answer"]
            assert len(result["citations"]) == 1
    
    @patch('src.agent.llm_factory.get_llm')
    def test_agent_no_results(self, mock_get_llm):
        """Test agent with no search results - robust to any number of LLM calls."""
        # Mock LLM that always returns a valid response
        def llm_side_effect(messages, **kwargs):
            prompt = messages[-1].content if messages else ""
            if "answer" in prompt:
                return AIMessage(content='{"answer": "No information found", "citations": []}')
            elif "slots" in prompt:
                return AIMessage(content='{"slots": [], "filled": [], "need_more": false, "new_queries": []}')
            else:
                return AIMessage(content='["test query"]')
        mock_llm = Mock()
        mock_llm.invoke.side_effect = llm_side_effect
        mock_get_llm.return_value = mock_llm

        # Mock search tool with no results
        with patch('src.agent.tools.get_search_tool') as mock_get_tool:
            mock_tool = Mock()
            mock_tool._arun = AsyncMock(return_value=[])
            mock_get_tool.return_value = mock_tool

            result = run_agent_sync("What is XYZ?", mock_llm, thread_id="test-thread-no-results")
            assert "No information found" in result["answer"]
    
    @patch('src.agent.llm_factory.get_llm')
    def test_agent_http_429_error(self, mock_get_llm):
        """Test agent handling HTTP 429 error."""
        # Mock LLM
        mock_llm = Mock()
        mock_llm.invoke.side_effect = [
            AIMessage(content='["test query"]'),  # generate_queries
            AIMessage(content='{"slots": ["definition"], "filled": [], "need_more": false, "new_queries": []}'),  # reflect
            AIMessage(content='{"answer": "Error occurred", "citations": []}')  # synthesize
        ]
        mock_get_llm.return_value = mock_llm
        
        # Mock search tool with HTTP 429 error
        with patch('src.agent.tools.get_search_tool') as mock_get_tool:
            mock_tool = Mock()
            mock_tool._arun = AsyncMock(side_effect=Exception("Rate limit exceeded"))
            mock_get_tool.return_value = mock_tool
            
            result = run_agent_sync("What is Python?", mock_llm, thread_id="test-thread-429")
            
            assert "Error" in result["answer"]
    
    @patch('src.agent.llm_factory.get_llm')
    def test_agent_timeout_error(self, mock_get_llm):
        """Test agent handling timeout error."""
        # Mock LLM
        mock_llm = Mock()
        mock_llm.invoke.side_effect = [
            AIMessage(content='["test query"]'),  # generate_queries
            AIMessage(content='{"slots": ["definition"], "filled": [], "need_more": false, "new_queries": []}'),  # reflect
            AIMessage(content='{"answer": "Error occurred", "citations": []}')  # synthesize
        ]
        mock_get_llm.return_value = mock_llm
        
        # Mock search tool with timeout error
        with patch('src.agent.tools.get_search_tool') as mock_get_tool:
            mock_tool = Mock()
            mock_tool._arun = AsyncMock(side_effect=asyncio.TimeoutError("Search timeout"))
            mock_get_tool.return_value = mock_tool
            
            result = run_agent_sync("What is Python?", mock_llm, thread_id="test-thread-timeout")
            
            assert "Error" in result["answer"]
    
    @patch('src.agent.llm_factory.get_llm')
    def test_agent_two_round_supplement(self, mock_get_llm):
        """Test agent with two-round supplement (need more search)."""
        # Mock LLM with two rounds
        mock_llm = Mock()
        mock_llm.invoke.side_effect = [
            AIMessage(content='["initial query"]'),  # generate_queries
            AIMessage(content='{"slots": ["definition", "features"], "filled": ["definition"], "need_more": true, "new_queries": ["refined query"]}'),  # reflect round 1
            AIMessage(content='{"slots": ["definition", "features"], "filled": ["definition", "features"], "need_more": false, "new_queries": []}'),  # reflect round 2
            AIMessage(content='{"answer": "Final answer [1]", "citations": [{"id": 1, "title": "Source", "url": "http://example.com"}]}')  # synthesize
        ]
        mock_get_llm.return_value = mock_llm
        
        # Mock search tool
        with patch('src.agent.tools.get_search_tool') as mock_get_tool:
            mock_tool = Mock()
            mock_tool._arun = AsyncMock(return_value=[
                {"title": "Source", "snippet": "Information", "url": "http://example.com"}
            ])
            mock_get_tool.return_value = mock_tool
            
            result = run_agent_sync("What is Python?", mock_llm, thread_id="test-thread-two-round")
            
            assert "Final answer" in result["answer"]
    
    @patch('src.agent.llm_factory.get_llm')
    def test_agent_slot_aware_integration(self, mock_get_llm):
        """Test agent with slot-aware reflection integration."""
        # Mock LLM with slot-aware responses
        mock_llm = Mock()
        mock_llm.invoke.side_effect = [
            AIMessage(content='["world cup 2022 winner"]'),  # generate_queries
            AIMessage(content='{"slots": ["winner", "score", "date"], "filled": ["winner"], "need_more": true, "new_queries": ["Argentina France 2022 final score", "World Cup 2022 date"]}'),  # reflect round 1
            AIMessage(content='{"slots": ["winner", "score", "date"], "filled": ["winner", "score", "date"], "need_more": false, "new_queries": []}'),  # reflect round 2
            AIMessage(content='{"answer": "Argentina won the 2022 World Cup [1][2]", "citations": [{"id": 1, "title": "World Cup 2022", "url": "http://example.com"}, {"id": 2, "title": "Final Score", "url": "http://example2.com"}]}')  # synthesize
        ]
        mock_get_llm.return_value = mock_llm
        
        # Mock search tool
        with patch('src.agent.tools.get_search_tool') as mock_get_tool:
            mock_tool = Mock()
            mock_tool._arun = AsyncMock(return_value=[
                {"title": "World Cup 2022", "snippet": "Argentina won", "url": "http://example.com"},
                {"title": "Final Score", "snippet": "4-2 on penalties", "url": "http://example2.com"}
            ])
            mock_get_tool.return_value = mock_tool
            
            result = run_agent_sync("Who won the 2022 World Cup?", mock_llm, thread_id="test-thread-slot-aware")
            
            assert "Argentina won" in result["answer"]
    
    @patch('src.agent.llm_factory.get_llm')
    def test_agent_max_iterations_reached(self, mock_get_llm):
        """Test agent when max iterations are reached."""
        # Robust LLM mock: always returns a valid response
        def llm_side_effect(messages, **kwargs):
            prompt = messages[-1].content if messages else ""
            if "answer" in prompt:
                return AIMessage(content='{"answer": "Max iterations reached", "citations": []}')
            elif "slots" in prompt:
                return AIMessage(content='{"slots": ["info"], "filled": [], "need_more": true, "new_queries": ["query2"]}')
            else:
                return AIMessage(content='["test query"]')
        mock_llm = Mock()
        mock_llm.invoke.side_effect = llm_side_effect
        mock_get_llm.return_value = mock_llm

        # Mock search tool
        with patch('src.agent.tools.get_search_tool') as mock_get_tool:
            mock_tool = Mock()
            mock_tool._arun = AsyncMock(return_value=[])
            mock_get_tool.return_value = mock_tool

            result = run_agent_sync("What is XYZ?", mock_llm, thread_id="test-thread-max-iterations")
            assert "Max iterations reached" in result["answer"]
    
    def test_should_continue_slot_validation(self):
        """Test should_continue with strict slot validation."""
        # Create a test state
        state = AgentState(question="Who won the 2022 World Cup?")
        
        # Test case 1: All slots filled
        state.slots = ["winner", "opponent", "score"]
        state.filled_slots = ["winner", "opponent", "score"]
        state.need_more = False
        state.new_queries = []
        
        result = should_continue(state)
        assert result == "synthesize"
        
        # Test case 2: Missing slots
        state.filled_slots = ["winner"]
        state.new_queries = ["opponent score 2022 World Cup"]
        
        result = should_continue(state)
        assert result == "continue"
        
        # Test case 3: No slots identified
        state.slots = []
        state.filled_slots = []
        state.need_more = True
        state.new_queries = ["test query"]
        
        result = should_continue(state)
        assert result == "continue"


if __name__ == "__main__":
    pytest.main([__file__]) 