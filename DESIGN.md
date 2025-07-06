# LLM Research Agent - Design Document

## Executive Summary

The LLM Research Agent is a LangGraph-based system that automates the research process by breaking down questions into search queries, gathering information from the web, reflecting on the completeness of results, and synthesizing concise answers with proper citations. The system supports up to 2 iterations of refinement and can operate both online (with Bing Search API) and offline (with mock data).

## Architecture Overview

### Core Components

1. **State Management** (`src/agent/state.py`)
   - Centralized state using dataclasses
   - Tracks question, queries, documents, reflection state, and final output
   - Maintains iteration count and maximum iteration limits

2. **LangGraph Pipeline** (`src/agent/graph.py`)
   - Four main nodes: GenerateQueries → WebSearchTool → Reflect → Synthesize
   - Conditional routing based on reflection results
   - Support for up to 2 iterations with refined queries

3. **LLM Integration** (`src/agent/llm_factory.py`)
   - Multi-provider support (OpenAI GPT, Google Gemini)
   - Environment-based configuration
   - Fallback mechanisms for API failures

4. **Search Tools** (`src/agent/tools.py`)
   - Bing Web Search API integration
   - Mock search tool for offline development
   - Concurrent query execution with deduplication

### Data Flow

```
Question Input
     ↓
GenerateQueries Node
     ↓
[3-5 Search Queries]
     ↓
WebSearchTool Node (Concurrent)
     ↓
[Merged & Deduplicated Results]
     ↓
Reflect Node
     ↓
{need_more: bool, new_queries: []}
     ↓
Conditional Routing
     ↓
Synthesize Node (if complete)
     ↓
{answer: string, citations: []}
```

## Detailed Component Design

### 1. State Management

**File**: `src/agent/state.py`

The `AgentState` dataclass serves as the central state container:

```python
@dataclass
class AgentState:
    question: str                    # Original input question
    queries: List[str]              # Generated search queries
    docs: List[Dict[str, Any]]      # Search results
    need_more: bool                 # Reflection decision
    new_queries: List[str]          # Refined queries if needed
    answer: str                     # Final synthesized answer
    citations: List[str]            # Source citations
    iteration: int                  # Current iteration count
    max_iterations: int             # Maximum allowed iterations
    messages: List[BaseMessage]     # LLM conversation history
```

**Design Rationale**:
- Immutable state updates prevent race conditions
- Clear separation of concerns between different data types
- Support for conversation history enables future enhancements

### 2. Node Implementations

#### GenerateQueries Node

**File**: `src/agent/nodes.py` - `generate_queries()`

**Purpose**: Break down the original question into 3-5 specific search queries

**Process**:
1. Format question using `GENERATE_QUERIES_PROMPT`
2. Invoke LLM with structured prompt
3. Parse JSON response containing query array
4. Fallback to original question if parsing fails

**Error Handling**:
- JSON parsing errors → fallback to original question
- LLM API errors → fallback to original question
- Empty responses → fallback to original question

#### WebSearchTool Node

**File**: `src/agent/nodes.py` - `web_search_tool()`

**Purpose**: Execute concurrent web searches and merge results

**Process**:
1. Check if queries exist in state
2. Execute all queries concurrently using `asyncio.gather()`
3. Merge results and deduplicate by URL
4. Handle individual query failures gracefully

**Performance Optimizations**:
- Concurrent execution reduces total search time
- URL-based deduplication prevents redundant information
- Exception handling per query prevents total failure

#### Reflect Node

**File**: `src/agent/nodes.py` - `reflect()`

**Purpose**: Evaluate search results and decide if more information is needed

**Process**:
1. Format search results for LLM consumption
2. Invoke LLM with `REFLECT_PROMPT`
3. Parse JSON response: `{need_more: bool, new_queries: []}`
4. Fallback logic based on result count

**Decision Logic**:
- If `need_more: false` → proceed to synthesize
- If `need_more: true` and `new_queries` not empty → continue iteration
- If `need_more: true` but no new queries → proceed to synthesize

#### Synthesize Node

**File**: `src/agent/nodes.py` - `synthesize()`

**Purpose**: Create final concise answer with citations

**Process**:
1. Format all search results for LLM
2. Invoke LLM with `SYNTHESIZE_PROMPT`
3. Parse JSON response: `{answer: string, citations: []}`
4. Ensure answer is ≤80 words with Markdown citations

**Quality Constraints**:
- Maximum 80 words (≈400 characters)
- Must include Markdown citations [1][2]...
- Citations array must match referenced sources

### 3. Search Tool Architecture

#### BingWebSearchTool

**File**: `src/agent/tools.py`

**Features**:
- Async HTTP requests using `aiohttp`
- Proper error handling for rate limits (HTTP 429)
- Structured response parsing
- Environment-based API key configuration

**API Integration**:
```python
endpoint = "https://api.bing.microsoft.com/v7.0/search"
headers = {"Ocp-Apim-Subscription-Key": api_key}
params = {"q": query, "count": 5, "mkt": "en-US"}
```

#### MockWebSearchTool

**File**: `src/agent/tools.py`

**Features**:
- Predefined mock data for common queries
- Simulated network delays for realistic testing
- Fallback responses for unknown queries
- Safe offline development environment

**Mock Data Structure**:
```python
mock_data = {
    "python programming": [
        {
            "title": "Python Programming Language",
            "snippet": "Python is a high-level...",
            "url": "https://python.org",
            "query": "python programming"
        }
    ]
}
```

### 4. LangGraph Pipeline Design

**File**: `src/agent/graph.py`

**Graph Structure**:
```
generate_queries → web_search → reflect → [conditional] → synthesize
                                    ↓
                              update_iteration → web_search
```

**Conditional Routing**:
- `should_continue()` function determines next step
- Routes to `update_iteration` if more search needed
- Routes to `synthesize` if complete or max iterations reached

**State Persistence**:
- Memory-based checkpointing for conversation continuity
- Supports future enhancements like conversation history

## Prompt Engineering

### GenerateQueries Prompt

**Goal**: Convert natural language questions into specific search queries

**Key Features**:
- Clear instructions for 3-5 queries
- Emphasis on specificity and different approaches
- Structured JSON output requirement
- Fallback handling instructions

### Reflect Prompt

**Goal**: Evaluate search result completeness and determine need for additional queries

**Key Features**:
- Structured evaluation criteria
- Clear decision framework
- JSON output format specification
- Fallback logic for edge cases

### Synthesize Prompt

**Goal**: Create concise, factual answers with proper citations

**Key Features**:
- Word limit enforcement (80 words)
- Citation format requirements
- Factual accuracy emphasis
- Source attribution guidelines

## Error Handling Strategy

### 1. LLM API Failures

**Handling**:
- Graceful degradation to fallback responses
- Logging of errors for debugging
- Continuation of pipeline with degraded results

**Fallbacks**:
- GenerateQueries: Use original question
- Reflect: Base decision on result count
- Synthesize: Create simple answer from available data

### 2. Search API Failures

**Handling**:
- Individual query failures don't stop entire pipeline
- Rate limiting detection and handling
- Timeout management with configurable limits

**Fallbacks**:
- Empty result sets trigger reflection
- Mock search tool for offline development
- Graceful degradation to available results

### 3. JSON Parsing Failures

**Handling**:
- Try-catch blocks around all JSON parsing
- Fallback to reasonable defaults
- Logging of parsing errors for debugging

## Performance Considerations

### 1. Concurrent Execution

**Implementation**:
- `asyncio.gather()` for parallel search queries
- Non-blocking I/O operations
- Configurable timeout limits

**Benefits**:
- Reduced total execution time
- Better resource utilization
- Improved user experience

### 2. Result Deduplication

**Strategy**:
- URL-based deduplication
- Maintains result quality
- Prevents redundant information

### 3. Iteration Limits

**Implementation**:
- Maximum 2 iterations by default
- Configurable via state parameters
- Prevents infinite loops

## Security Considerations

### 1. API Key Management

**Implementation**:
- Environment variable configuration
- No hardcoded credentials
- Secure key handling practices

### 2. Input Validation

**Implementation**:
- Question sanitization
- Query length limits
- URL validation for search results

### 3. Error Information

**Implementation**:
- Limited error details in production
- Debug logging for development
- Safe error messages for users

## Testing Strategy

### 1. Unit Tests

**Coverage**:
- Individual node functionality
- Error handling scenarios
- Edge case handling
- Mock data validation

### 2. Integration Tests

**Coverage**:
- End-to-end pipeline execution
- Multi-iteration scenarios
- Error recovery mechanisms
- Performance benchmarks

### 3. Test Cases

**Required Scenarios**:
1. Happy path with good results
2. No search results found
3. HTTP 429 rate limiting
4. Network timeout errors
5. Two-round supplement scenarios

## Deployment Architecture

### 1. Docker Containerization

**Benefits**:
- Consistent runtime environment
- Easy deployment and scaling
- Isolated dependencies
- Version control for deployments

### 2. Environment Configuration

**Variables**:
- `OPENAI_API_KEY`: OpenAI API access
- `GEMINI_API_KEY`: Google Gemini API access
- `BING_API_KEY`: Bing Search API access

### 3. Docker Compose

**Features**:
- Service definition
- Environment variable injection
- Volume mounting for development
- Easy local testing

## Future Enhancements

### 1. Slot-Aware Reflection

**Concept**: Advanced reflection that tracks specific information slots

**Implementation**:
```python
{
    "slots": ["winner", "score", "date"],
    "filled": ["winner"],
    "need_more": true,
    "new_queries": ["argentina goals 2022 final"]
}
```

### 2. Caching Layer

**Implementation**:
- Redis-based LRU cache
- Query result caching
- Configurable TTL

### 3. Streaming Support

**Implementation**:
- Server-Sent Events (SSE)
- Real-time progress updates
- WebSocket support for interactive sessions

### 4. Metrics and Monitoring

**Implementation**:
- OpenTelemetry integration
- Prometheus metrics
- Distributed tracing
- Performance monitoring

## Conclusion

The LLM Research Agent provides a robust, scalable foundation for automated research tasks. The modular architecture enables easy extension and customization, while the comprehensive error handling ensures reliable operation in production environments. The system successfully balances performance, accuracy, and maintainability while providing a clear path for future enhancements. 