# API Conventions
 
- All endpoints are async
- Request and response bodies are Pydantic models from schemas/
- Routes are in api/routes_<feature>.py and registered in main.py
- Long-running tasks: return job_id, stream progress as Server-Sent Events
- Errors return RFC 7807 problem-details JSON
- Every route has at least one test in tests/test_api/
