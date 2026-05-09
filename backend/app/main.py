from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_papers, routes_research
from app.core.config import get_settings

_settings = get_settings()

app = FastAPI(title="CorpusAI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_research.router)
app.include_router(routes_papers.router)


@app.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "model": settings.anthropic_chat_model,
        "api_key_configured": "yes" if settings.anthropic_api_key else "no",
    }
