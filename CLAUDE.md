# CorpusAI — Academic Multi-Agent Assistant
 
## What this is
A web app that generates academic research papers section by section
using a team of specialised AI agents. The user provides a topic and
parameters; the system returns a paper with Abstract, Introduction,
Methods, Results, Discussion, and References.
 
## Stack
- Backend:  Python 3.11, FastAPI, Microsoft Agent Framework 1.0
- Frontend: Next.js 14 (App Router), TypeScript, Tailwind
- LLM:      Anthropic Claude via agent-framework-anthropic
- Package manager (Python): uv
- Package manager (Node):   npm
- Shell:    Git Bash on Windows ARM64
 
## Architecture (today)
Monolith. One FastAPI service, one Next.js app. Agents live in
backend/app/agents/. Each agent has a .py class and a .md prompt
file in backend/app/prompts/. The orchestrator uses MAF's graph-based
Workflow with sequential edges (Research -> Abstract -> Introduction
-> Methods -> Results -> Discussion -> Reference -> Editor).
 
## Conventions
- Every agent inherits from BaseAgent in agents/base.py
- Prompts live in prompts/*.md — never hardcode prompts in Python
- All agent I/O uses Pydantic models from schemas/
- Async everywhere on the backend
- Type hints on every public function
- Use MAF's AnthropicClient — do NOT call the Anthropic SDK directly
  from agents (the framework handles retries, telemetry, tool loops)
 
## How to run
- Backend:  cd backend && uv run uvicorn app.main:app --reload
- Frontend: cd frontend && npm run dev
- Tests:    cd backend && uv run pytest
 
## Things you should never do
- Don't hardcode API keys — use .env
- Don't change the BaseAgent contract without updating all subclasses
- Don't commit CLAUDE.local.md or .env
- Don't let agents call each other directly — go through the Workflow
- Don't skip writing a test when adding a new agent
- Don't push directly to main — use a feature branch
 
## See also
- .claude/rules/agent-conventions.md
- .claude/rules/api-conventions.md
