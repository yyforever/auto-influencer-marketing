# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Auto Influencer Marketing Platform** - an AI-powered system that leverages LangGraph agents to perform comprehensive research and analysis for influencer marketing campaigns. The platform uses advanced web research capabilities to gather market intelligence, analyze trends, and provide data-driven insights for marketing decisions.

**Core Value Proposition**: Automated research and analysis for influencer marketing campaigns, powered by Google Gemini AI and LangGraph orchestration.

**Key Capabilities**:
- Automated web research with iterative refinement
- Knowledge gap identification and progressive search enhancement
- Real-time streaming results with citation management
- Scalable agent architecture for complex research workflows

## Architecture

### Backend (`backend/`)
- **Technology Stack**: LangGraph + FastAPI + Google Gemini AI
- **Entry Point**: `src/agent/graph.py` - Defines the main research agent workflow
- **Agent Flow**: Query Generation → Web Research (Parallel) → Reflection → Evaluation → Finalize Answer
- **State Management**: TypedDict-based state system with immutable updates in `src/agent/state.py`
- **Configuration**: LangGraph configuration in `langgraph.json`, Python dependencies in `pyproject.toml`
- **Static Frontend Serving**: `src/agent/app.py` serves the built React frontend at `/app` route

**LangGraph Architecture Details**:
- **Parallel Processing**: Web research nodes execute concurrently using `Send` mechanism
- **State Persistence**: Uses Redis for pub-sub and Postgres for state management in production
- **Streaming**: Real-time results streaming via LangGraph's streaming capabilities
- **Error Handling**: Implements retry logic and graceful degradation
- **Token Optimization**: URL shortening and efficient prompt formatting
- **You should always search langgraph-llms-full.txt to make sure usage of LangGraph is best practice. It's a very long text.

### Frontend (`frontend/`)
- **Technology**: React 19 + TypeScript + Vite + Tailwind CSS + Shadcn UI
- **Architecture**: Single-page app with real-time streaming from LangGraph backend
- **Main Component**: `src/App.tsx` handles streaming, state management, and routing
- **UI Components**: Located in `src/components/` using Shadcn UI patterns
- **LangGraph Integration**: Uses `@langchain/langgraph-sdk/react` for streaming

### Key Agent Workflow (LangGraph)
1. **generate_query**: Creates search queries using Gemini models with structured output
2. **web_research**: Performs web research with Google Search API (parallel execution via Send)
3. **reflection**: Analyzes results and identifies knowledge gaps using reasoning models
4. **evaluate_research**: Routing function to continue research or finalize based on sufficiency
5. **finalize_answer**: Synthesizes final answer with citations and URL replacement

**State Flow Details**:
- **OverallState**: Accumulates messages, queries, results, and sources
- **Parallel Execution**: Multiple web_research nodes run concurrently for different queries
- **Iterative Refinement**: Research loop continues until knowledge gaps are filled or max loops reached
- **Citation Management**: URLs are shortened for token efficiency and restored in final output

## LangGraph Development Guide

### Understanding State Management
```python
# State updates are additive, not replacement
state["web_research_result"] = [new_result]  # Adds to existing results
state["sources_gathered"] = [new_sources]    # Accumulates sources
```

### Debugging LangGraph Flows
```bash
# ALWAYS activate virtual environment first:
cd backend
source .venv/bin/activate

# Enable detailed logging
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"

# Use LangGraph dev server for debugging
langgraph dev
# Access LangGraph Studio at http://localhost:2024
```

### Performance Optimization
- **Parallel Processing**: Use `Send` for concurrent node execution
- **Token Management**: Implement URL shortening and efficient prompt formatting
- **Caching**: Consider implementing result caching for repeated queries
- **Streaming**: Use streaming for real-time user feedback

### Common LangGraph Patterns
- **Conditional Routing**: `evaluate_research` demonstrates conditional edge logic
- **Parallel Execution**: `continue_to_web_research` shows parallel node spawning
- **State Accumulation**: Results accumulate across multiple iterations
- **Error Recovery**: Implement retry logic with `max_retries` parameter

## Development Commands

### Setup
```bash
# Backend dependencies
cd backend && pip install .

# Frontend dependencies  
cd frontend && npm install

# Environment setup
cp backend/.env.example backend/.env
# Add your GEMINI_API_KEY to backend/.env
```

### Virtual Environment Activation (CRITICAL)
```bash
# ALWAYS activate the backend virtual environment before running Python commands
# From project root directory:
source backend/.venv/bin/activate

# Verify correct Python path:
which python
# Should output: /Users/yangyang/Github/auto-influencer-marketing/backend/.venv/bin/python

# This is REQUIRED for:
# - Running Python scripts
# - Testing imports
# - LangGraph development
# - CLI testing
# - Any Python-dependent commands
```

### Development Servers
```bash
# Start both servers (recommended)
make dev

# Or start individually:
make dev-backend  # Starts LangGraph dev server on port 2024
make dev-frontend # Starts Vite dev server on port 5173
```

### Backend Testing & Linting
```bash
cd backend

# Run tests
make test
make test_watch  # Watch mode

# Linting and formatting
make lint        # Full linting (ruff + mypy)
make format      # Format code
uv run ruff check .              # Quick lint
uv run ruff format .             # Quick format
```

### Frontend Linting & Building
```bash
cd frontend

# Linting
npm run lint

# Building
npm run build    # Creates dist/ for production
```

### CLI Testing
```bash
# ALWAYS activate virtual environment first:
cd backend
source .venv/bin/activate
python examples/cli_research.py "Your research question"
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. LangGraph Development Issues
**Problem**: LangGraph dev server fails to start
```bash
# Check if port 2024 is available
lsof -i :2024
# Kill process if necessary
kill -9 <PID>
```

**Problem**: State persistence errors
```bash
# Verify Redis/Postgres in production
docker-compose ps
# Check environment variables
env | grep -E "(REDIS|POSTGRES)"
```

#### 2. API and Authentication Issues
**Problem**: Gemini API key errors
```bash
# Verify API key is set
echo $GEMINI_API_KEY
# Check key format (should start with 'AIza')
```

**Problem**: Rate limiting or quota exceeded
- Implement exponential backoff in retry logic
- Consider request batching for multiple queries
- Monitor API usage in Google Cloud Console

#### 3. Performance Issues
**Problem**: Slow response times
- Check parallel execution in web_research nodes
- Verify token optimization (URL shortening)
- Monitor LangSmith traces for bottlenecks

**Problem**: Memory issues with large state
- Implement state cleanup after research loops
- Consider pagination for large result sets
- Monitor state size in production

#### 4. Frontend Integration Issues
**Problem**: Streaming not working
```bash
# Check WebSocket connection
# Verify apiUrl in App.tsx matches backend
# Check CORS settings in FastAPI
```

**Problem**: Real-time updates not appearing
- Verify `onUpdateEvent` handlers in React
- Check LangGraph streaming configuration
- Monitor browser console for errors

### Debugging Best Practices

#### LangSmith Integration
```python
# Add debugging metadata to traces
config = {
    "tags": ["debug", "influencer-marketing"],
    "metadata": {"user_id": "test", "query_type": "market_research"}
}
graph.invoke(inputs, config)
```

#### Local Development
```bash
# ALWAYS activate virtual environment first:
cd backend
source .venv/bin/activate

# Enable verbose logging
export LANGCHAIN_VERBOSE=true
export LANGCHAIN_TRACING_V2=true

# Monitor resource usage
htop  # CPU/Memory monitoring
```

### Performance Monitoring
- **LangSmith**: Use for trace analysis and performance optimization
- **Application Metrics**: Monitor API response times and error rates
- **Resource Usage**: Track memory and CPU usage during research loops
- **Token Usage**: Monitor Gemini API token consumption

## Configuration

### Environment Variables
- **GEMINI_API_KEY**: Required for backend agent functionality
- **LANGSMITH_API_KEY**: Optional, for LangSmith tracing (production deployments)

### Agent Configuration
- **Models**: Configurable in `src/agent/configuration.py`
- **Research Parameters**: Initial query count, max research loops, reasoning models
- **Frontend Config**: API URL switches between dev (port 2024) and production (port 8123)

### LangGraph Configuration (`backend/langgraph.json`)
- **Graph**: Points to `src/agent/graph.py:graph`
- **HTTP App**: Points to `src/agent/app.py:app`
- **Environment**: Uses `.env` file

## Production Deployment

The project includes Docker configuration:
- **Dockerfile**: Builds production image with frontend and backend
- **docker-compose.yml**: Includes Redis and Postgres for LangGraph deployment
- **Frontend Serving**: Backend serves static frontend build at `/app` route

### Security Best Practices

#### API Key Management
```bash
# Use environment variables, never hardcode keys
export GEMINI_API_KEY="your_key_here"
export LANGSMITH_API_KEY="your_key_here"

# For production, use secure key management
# - AWS Secrets Manager
# - Azure Key Vault
# - Google Secret Manager
```

#### Input Validation
```python
# Implement input sanitization to prevent prompt injection
def sanitize_user_input(user_input: str) -> str:
    # Remove potentially harmful patterns
    # Limit input length
    # Validate input format
    pass
```

#### Rate Limiting
```python
# Implement rate limiting for API endpoints
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/research")
@limiter.limit("10/minute")
async def research_endpoint():
    pass
```

#### Error Handling
```python
# Don't expose internal errors to clients
try:
    result = llm.invoke(prompt)
except Exception as e:
    logger.error(f"LLM error: {e}")
    raise HTTPException(status_code=500, detail="Research service unavailable")
```

### Deployment Checklist
- [ ] Environment variables configured securely
- [ ] API keys rotated and stored securely
- [ ] Input validation implemented
- [ ] Rate limiting configured
- [ ] Error handling implemented
- [ ] Logging configured for production
- [ ] Health checks implemented
- [ ] Monitoring and alerting set up
- [ ] Backup strategy for state data
- [ ] SSL/TLS certificates configured

## Important File Patterns

### Backend State System
- **OverallState**: Main graph state with messages, queries, results, sources
- **ReflectionState**: Intermediate state for research evaluation
- **QueryGenerationState & WebSearchState**: Specialized states for specific nodes

### Frontend Components
- **App.tsx**: Main component with streaming logic and state management
- **WelcomeScreen**: Initial interface for starting research
- **ChatMessagesView**: Chat interface showing conversation and research progress
- **ActivityTimeline**: Real-time display of agent research steps

### Backend Tools & Utilities
- **tools_and_schemas.py**: Pydantic schemas for structured LLM outputs
- **prompts.py**: Prompt templates for different agent steps
- **utils.py**: Citation handling, URL resolution, research topic extraction

## Extension Guide for Influencer Marketing Features

### Adding New Research Types

#### 1. Influencer Discovery
```python
# Add new node to graph.py
def influencer_discovery(state: OverallState, config: RunnableConfig):
    """Find relevant influencers based on niche and metrics"""
    search_query = f"top influencers in {state['niche']} {state['platform']}"
    # Implementation for influencer search
```

#### 2. Trend Analysis
```python
# Add trend analysis node
def trend_analysis(state: OverallState, config: RunnableConfig):
    """Analyze current trends in influencer marketing"""
    # Implementation for trend identification
```

#### 3. Competitor Analysis
```python
# Add competitor research node
def competitor_analysis(state: OverallState, config: RunnableConfig):
    """Research competitor influencer strategies"""
    # Implementation for competitor analysis
```

### Extending State Management

#### Custom State Types
```python
# Add to state.py
class InfluencerState(TypedDict):
    influencer_profiles: Annotated[list, operator.add]
    engagement_metrics: Annotated[list, operator.add]
    collaboration_history: Annotated[list, operator.add]

class CampaignState(TypedDict):
    campaign_goals: str
    target_audience: dict
    budget_constraints: dict
    timeline: dict
```

### Adding New Prompt Templates

#### Influencer-Specific Prompts
```python
# Add to prompts.py
influencer_discovery_instructions = """
You are an expert in influencer marketing research. 
Your task is to find relevant influencers for a {campaign_type} campaign.

Research parameters:
- Target niche: {niche}
- Platform: {platform}
- Audience size: {audience_size}
- Engagement rate: {min_engagement_rate}
- Budget range: {budget_range}

Focus on finding influencers who:
1. Align with brand values
2. Have authentic engagement
3. Match target demographics
4. Are within budget constraints
"""
```

### Custom Tools Integration

#### Social Media APIs
```python
# Add social media monitoring tools
@tool
def instagram_metrics(username: str) -> dict:
    """Get Instagram influencer metrics"""
    # Implementation for Instagram API
    pass

@tool
def tiktok_trends(hashtag: str) -> dict:
    """Get TikTok trend analysis"""
    # Implementation for TikTok API
    pass
```

### Frontend Extensions

#### New Components for Influencer Marketing
```typescript
// Add to components/
interface InfluencerProfile {
  username: string;
  platform: string;
  followers: number;
  engagement_rate: number;
  niche: string;
  contact_info: string;
}

const InfluencerCard: React.FC<{profile: InfluencerProfile}> = ({profile}) => {
  // Component implementation
};
```

### Configuration Extensions

#### Marketing-Specific Settings
```python
# Add to configuration.py
class MarketingConfiguration:
    influencer_discovery_count: int = 10
    trend_analysis_depth: int = 3
    competitor_analysis_count: int = 5
    engagement_threshold: float = 0.03
    budget_optimization: bool = True
```

### Database Schema for Campaign Management

#### Campaign Tracking
```sql
-- Add to database schema
CREATE TABLE campaigns (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    goals TEXT,
    target_audience JSONB,
    budget_constraints JSONB,
    timeline JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE influencer_matches (
    id UUID PRIMARY KEY,
    campaign_id UUID REFERENCES campaigns(id),
    influencer_data JSONB,
    match_score FLOAT,
    engagement_predictions JSONB
);
```

### API Endpoints for Marketing Features

#### Campaign Management Endpoints
```python
# Add to app.py
@app.post("/campaigns")
async def create_campaign(campaign: CampaignCreate):
    """Create new influencer marketing campaign"""
    pass

@app.get("/campaigns/{campaign_id}/influencers")
async def get_campaign_influencers(campaign_id: str):
    """Get influencer recommendations for campaign"""
    pass

@app.post("/campaigns/{campaign_id}/analyze")
async def analyze_campaign_performance(campaign_id: str):
    """Analyze campaign performance metrics"""
    pass
```

## Best Practices for Extensions

### Code Organization
- Keep marketing-specific logic in separate modules
- Use dependency injection for external APIs
- Implement proper error handling for third-party services
- Add comprehensive logging for debugging

### Testing Strategy
- Unit tests for each new node
- Integration tests for API endpoints
- Mock external API calls
- Test state management with various scenarios

### Performance Considerations
- Cache frequently accessed influencer data
- Implement pagination for large result sets
- Use background tasks for time-consuming analyses
- Monitor API rate limits for social media platforms

## Quick Reference

### Essential Commands
```bash
# CRITICAL: Always activate virtual environment for backend work
source backend/.venv/bin/activate

# Development setup
make dev                                    # Start both servers
cd backend && langgraph dev                # LangGraph Studio  
cd frontend && npm run dev                 # Frontend only

# Testing and quality (with .venv activated)
cd backend && make test                    # Run tests
cd backend && make lint                    # Lint code
cd frontend && npm run lint                # Frontend lint

# Debugging (with .venv activated)
export LANGCHAIN_TRACING_V2=true          # Enable tracing
export LANGCHAIN_VERBOSE=true             # Verbose logging
```

### Common Workflows

#### 1. Adding a New Research Node
```python
# 1. Define the node function in graph.py
def new_research_node(state: OverallState, config: RunnableConfig):
    """New research functionality"""
    pass

# 2. Add to graph builder
builder.add_node("new_research_node", new_research_node)

# 3. Add edges
builder.add_edge("reflection", "new_research_node")
builder.add_edge("new_research_node", "finalize_answer")

# 4. Update state types if needed in state.py
```

#### 2. Modifying Prompts
```python
# 1. Edit prompts.py
new_prompt_template = """
Your specialized prompt here with {variables}
"""

# 2. Update node to use new prompt
formatted_prompt = new_prompt_template.format(
    variable1=state["value1"],
    variable2=state["value2"]
)
```

#### 3. Adding Frontend Components
```typescript
// 1. Create component in src/components/
export const NewComponent: React.FC<Props> = ({props}) => {
  // Implementation
};

// 2. Add to main App.tsx
import { NewComponent } from './components/NewComponent';

// 3. Use in render
<NewComponent {...props} />
```

### Key File Locations
- **Graph Definition**: `backend/src/agent/graph.py`
- **State Management**: `backend/src/agent/state.py`
- **Prompts**: `backend/src/agent/prompts.py`
- **Configuration**: `backend/src/agent/configuration.py`
- **Frontend Main**: `frontend/src/App.tsx`
- **UI Components**: `frontend/src/components/`
- **Environment**: `backend/.env`

### Important URLs
- **Development Frontend**: `http://localhost:5173`
- **LangGraph Studio**: `http://localhost:2024`
- **Production Frontend**: `http://localhost:8123/app`
- **API Endpoints**: `http://localhost:8123` (production) or `http://localhost:2024` (dev)

### Environment Variables Reference
```bash
# Required
GEMINI_API_KEY=your_gemini_key

# Optional
LANGSMITH_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_VERBOSE=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

## Development Tips

### LangGraph Best Practices
1. **Use Send for Parallel Processing**: Leverage parallel execution for independent operations
2. **Implement Proper Error Handling**: Use try-catch blocks and retry logic
3. **Optimize State Management**: Keep state updates immutable and efficient
4. **Monitor Performance**: Use LangSmith for tracing and optimization
5. **Test Thoroughly**: Write unit tests for each node and integration tests for flows

### Common Pitfalls
- **State Mutation**: Always return new state objects, don't modify in place
- **Blocking Operations**: Use async/await for I/O operations
- **Memory Leaks**: Clean up resources and avoid circular references
- **API Rate Limits**: Implement exponential backoff and request throttling
- **Error Propagation**: Handle errors gracefully without breaking the entire flow

### Resources
- **LangGraph Documentation**: `@langgraph-llms-full.txt`
- **LangSmith Platform**: https://smith.langchain.com
- **Google Gemini API**: https://ai.google.dev/docs
- **Project Repository**: https://github.com/yyforever/auto-influencer-marketing