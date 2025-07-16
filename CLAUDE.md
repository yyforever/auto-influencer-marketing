# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an auto-influencer marketing platform project (forked from a Google Gemini LangGraph quickstart). The project consists of a React frontend and a LangGraph-powered backend agent system.

## Architecture

### Backend (`backend/`)
- **Technology**: LangGraph + FastAPI + Google Gemini AI
- **Entry Point**: `src/agent/graph.py` - Defines the main research agent workflow
- **Agent Flow**: Query Generation → Web Research → Reflection → Finalize Answer
- **State Management**: TypedDict-based state system in `src/agent/state.py`
- **Configuration**: LangGraph configuration in `langgraph.json`, Python dependencies in `pyproject.toml`
- **Static Frontend Serving**: `src/agent/app.py` serves the built React frontend at `/app` route

### Frontend (`frontend/`)
- **Technology**: React 19 + TypeScript + Vite + Tailwind CSS + Shadcn UI
- **Architecture**: Single-page app with real-time streaming from LangGraph backend
- **Main Component**: `src/App.tsx` handles streaming, state management, and routing
- **UI Components**: Located in `src/components/` using Shadcn UI patterns
- **LangGraph Integration**: Uses `@langchain/langgraph-sdk/react` for streaming

### Key Agent Workflow (LangGraph)
1. **generate_query**: Creates search queries using Gemini models
2. **web_research**: Performs web research with Google Search API (parallel execution)
3. **reflection**: Analyzes results and identifies knowledge gaps
4. **evaluate_research**: Routing function to continue research or finalize
5. **finalize_answer**: Synthesizes final answer with citations

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
cd backend
python examples/cli_research.py "Your research question"
```

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