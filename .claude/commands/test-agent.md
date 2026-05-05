Run a single agent end-to-end with a test input.
 
Ask me the agent name. Then:
1. Run pytest tests/test_agents/test_<name>.py with -v
2. If it passes, run the agent CLI:
   uv run python -m app.agents.<name> --topic "test topic"
3. Print the output and the token usage from MAF telemetry.
