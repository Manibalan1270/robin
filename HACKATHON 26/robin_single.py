import os
import uuid
import re
import json
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Tuple, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# --- CONFIGURATION ---
class Settings(BaseSettings):
    PROJECT_NAME: str = "Robin Chatbot API"
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_MODEL_MAIN: str = "gpt-4o"
    OPENAI_MODEL_FALLBACK: str = "gpt-3.5-turbo"
    OPENAI_TEMPERATURE_EMPATHY: float = 0.7
    OPENAI_TEMPERATURE_CRISIS: float = 0.2
    
    # Defaults for simplicity
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
    CORS_ORIGINS: List[str] = ["*"]
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Initialize app with safe defaults if .env is missing
try:
    settings = Settings()
except Exception:
    print("WARNING: .env file missing or incomplete. Please set OPENAI_API_KEY environment variable.")
    # For the purpose of providing a file that "runs", we allow it to init if key is in env
    class FallbackSettings:
        PROJECT_NAME = "Robin Chatbot API"
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        OPENAI_MODEL_MAIN = "gpt-4o"
        OPENAI_MODEL_FALLBACK = "gpt-3.5-turbo"
        OPENAI_TEMPERATURE_EMPATHY = 0.7
        OPENAI_TEMPERATURE_CRISIS = 0.2
        CORS_ORIGINS = ["*"]
    settings = FallbackSettings()

# --- SAFETY RESOURCES ---
INDIA_HELPLINES = {
    "NIMHANS": {"name": "NIMHANS Crisis Helpline", "number": "080-4611-0007", "hours": "24/7"},
    "KIRAN": {"name": "KIRAN Mental Health Helpline", "number": "1800-599-0019", "hours": "24/7"},
    "AASRA": {"name": "AASRA", "number": "91-22-2754-6669", "hours": "24/7"}
}

CRISIS_RESPONSE_TEMPLATE = """
I am detecting that you might be going through a very difficult time right now, and I want to prioritize your safety.

Please know that you are not alone. There are people who want to help:
{resources}

Please reach out to them. They are trained to listen and support you.
"""

# --- LOGIC MODULES ---
class CrisisDetector:
    KEYWORDS = {
        "die": 6, "suicide": 9, "kill myself": 10, "end my life": 10,
        "hurt myself": 8, "overdose": 9, "hopeless": 5
    }
    
    def detect(self, text: str) -> Tuple[bool, int, Optional[str]]:
        text_lower = text.lower()
        max_severity = 0
        for kw, sev in self.KEYWORDS.items():
            if kw in text_lower:
                max_severity = max(max_severity, sev)
        
        is_crisis = max_severity >= 7
        response = None
        if is_crisis:
            res_str = "\n".join([f"- **{v['name']}**: {v['number']} ({v['hours']})" for v in INDIA_HELPLINES.values()])
            response = CRISIS_RESPONSE_TEMPLATE.format(resources=res_str)
        
        return is_crisis, max_severity, response

class RobinPersonality:
    SYSTEM_PROMPT = """
    You are Robin, a highly compassionate and emotionally intelligent chatbot.
    Your tone is warm, validating, and non-judgmental.
    You help users navigate their emotions while maintaining healthy boundaries.
    Always prioritize empathy and active listening.
    Current Date: {date}
    """

# --- FASTAPI SETUP ---
app = FastAPI(title=settings.PROJECT_NAME)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
crisis_detector = CrisisDetector()

# --- MODELS ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    response: str
    emotion_detected: str = "neutral"
    crisis_flag: bool = False
    tokens_used: int = 0

# --- ENDPOINTS ---
@app.get("/health")
async def health():
    return {"status": "ok", "openai_key_set": bool(settings.OPENAI_API_KEY)}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API Key not configured")

    # 1. Crisis Detection (Pre-LLM)
    is_crisis, severity, crisis_msg = crisis_detector.detect(request.message)
    if is_crisis:
        return ChatResponse(
            response=crisis_msg,
            crisis_flag=True,
            emotion_detected="emergency"
        )

    # 2. OpenAI Call
    try:
        messages = [
            {"role": "system", "content": RobinPersonality.SYSTEM_PROMPT.format(date=datetime.now().date())}
        ]
        # Append history (limited to last 10 for performance/cost)
        messages.extend(request.history[-10:])
        messages.append({"role": "user", "content": request.message})

        response = await openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL_MAIN,
            messages=messages,
            temperature=settings.OPENAI_TEMPERATURE_EMPATHY,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens
        
        return ChatResponse(
            response=content,
            tokens_used=tokens
        )
    except Exception as e:
        # Fallback to GPT-3.5 or error
        print(f"Error in gemini: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            json_data = json.loads(data)
            user_msg = json_data.get("message", "")
            
            # Crisis check
            is_crisis, _, crisis_msg = crisis_detector.detect(user_msg)
            if is_crisis:
                await websocket.send_json({"response": crisis_msg, "crisis_flag": True})
                continue

            # Streaming response
            stream = await openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL_MAIN,
                messages=[
                    {"role": "system", "content": RobinPersonality.SYSTEM_PROMPT.format(date=datetime.now().date())},
                    {"role": "user", "content": user_msg}
                ],
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    await websocket.send_json({"response": chunk.choices[0].delta.content, "type": "chunk"})
            
            await websocket.send_json({"type": "done"})
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
