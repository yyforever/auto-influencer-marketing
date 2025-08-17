.PHONY: help dev-frontend dev-backend dev dev-frontend-silent dev-backend-silent dev-silent

help:
	@echo "Available commands:"
	@echo "  make dev-frontend    - Starts the frontend development server (Vite) with logs to logs/frontend.log"
	@echo "  make dev-backend     - Starts the backend development server (LangGraph) with logs to logs/backend.log"
	@echo "  make dev             - Starts both frontend and backend development servers with logging"
	@echo "  make dev-silent      - Starts both servers silently (logs only to files)"
	@echo "  make dev-frontend-silent - Frontend only, silent logging"
	@echo "  make dev-backend-silent  - Backend only, silent logging"

dev-frontend:
	@echo "Starting frontend development server..."
	@cd frontend && npm run dev 2>&1 | tee ../logs/frontend.log

dev-backend:
	@echo "Starting backend development server..."
	@cd backend && langgraph dev 2>&1 | tee ../logs/backend.log

# Run frontend and backend concurrently
dev:
	@echo "Starting both frontend and backend development servers..."
	@mkdir -p logs
	@make dev-frontend & make dev-backend

# New commands for logging without console output
dev-frontend-silent:
	@echo "Starting frontend development server (logging to logs/frontend.log)..."
	@mkdir -p logs
	@cd frontend && npm run dev > ../logs/frontend.log 2>&1

dev-backend-silent:
	@echo "Starting backend development server (logging to logs/backend.log)..."
	@mkdir -p logs
	@cd backend && langgraph dev > ../logs/backend.log 2>&1

dev-silent:
	@echo "Starting both servers silently (logs in logs/ directory)..."
	@mkdir -p logs
	@make dev-frontend-silent & make dev-backend-silent 