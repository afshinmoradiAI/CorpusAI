Add a new agent to the system following our conventions.
 
Steps:
1. Ask me the agent name and purpose if not provided.
2. Create backend/app/prompts/<name>.md with the system prompt.
3. Create backend/app/agents/<name>.py inheriting from BaseAgent and
   wrapping a MAF ChatAgent with AnthropicClient.
4. Register the agent in backend/app/agents/__init__.py.
5. Add the agent as a node in the orchestrator's Workflow.
6. Write a unit test in backend/tests/test_agents/test_<name>.py.
7. Show me the diff before committing.
 
Follow .claude/rules/agent-conventions.md strictly.
