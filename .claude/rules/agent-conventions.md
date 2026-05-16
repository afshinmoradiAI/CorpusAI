# Agent Conventions (PydanticAI)
 
Every agent MUST:
- Inherit from BaseAgent (agents/base.py)
- Declare `prompt_name` (maps to prompts/<name>.md) and `output_model`
- Load its system prompt via load_prompt() — never hardcode prompts in Python
- Accept and return Pydantic models — no raw dicts
- Be async (async def run)
- Have a corresponding test file in tests/test_agents/
- Be called from a workflow (explore.py or write.py), not from other agents
 
Every agent MUST NOT:
- Instantiate AnthropicModel, AnthropicProvider, or pydantic_ai.Agent directly —
  BaseAgent._get_agent() handles this
- Call another agent directly — go through the workflow functions
- Have business logic in the prompt file
- Use global state
- Catch exceptions silently — let them bubble to the workflow runtime
