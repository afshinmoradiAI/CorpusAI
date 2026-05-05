# Agent Conventions (Microsoft Agent Framework)
 
Every agent MUST:
- Inherit from BaseAgent
- Be wrapped as a MAF ChatAgent using AnthropicClient
- Load its system prompt from prompts/<name>.md via load_prompt()
- Accept and return Pydantic models — no raw dicts
- Be async (async def run)
- Have a corresponding test file in tests/test_agents/
- Be a node in the orchestrator's Workflow graph
 
Every agent MUST NOT:
- Call another agent directly — use the Workflow
- Have business logic in the prompt file
- Use global state
- Catch exceptions silently — let them bubble to the workflow runtime
