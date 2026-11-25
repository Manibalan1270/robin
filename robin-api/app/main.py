from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints.chat import router as chat_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION, "ai_configured": bool(settings.OPENAI_API_KEY)}


@app.get("/")
async def root():
    return {"message": "Welcome to Robin Chatbot API. See /docs for the API."}
