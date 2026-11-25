import json
import logging
from datetime import date
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.modules.crisis_detector import crisis_detector

logger = logging.getLogger("robin")
router = APIRouter()

SYSTEM_PROMPT = """You are Robin, a compassionate and emotionally intelligent companion.
Your tone is warm, validating and non-judgmental. Help people make sense of their emotions
while keeping healthy boundaries. You are not a therapist; gently suggest professional
help when it would genuinely help. If someone may be at risk of harming themselves,
respond with care and encourage them to contact these helplines in India:
{resources}
Today's date: {today}"""

CAREFUL_NOTE = (
    "The user's last message shows signs of distress (severity {severity}/10). "
    "Respond with extra warmth, check in on how they are doing, and mention support is available."
)

_client: Optional[AsyncOpenAI] = None


def get_client() -> AsyncOpenAI:
    """Creates the AI client on first use, so the app can start without a key."""
    global _client
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="Robin's AI is not configured (set OPENAI_API_KEY).")
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL or None,
        )
    return _client


class HistoryMessage(BaseModel):
    # Only user/assistant turns are accepted. Clients can no longer inject
    # their own "system" instructions into the conversation.
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=settings.MAX_MESSAGE_CHARS)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=settings.MAX_MESSAGE_CHARS)
    history: List[HistoryMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    response: str
    crisis_flag: bool = False
    severity: int = 0
    tokens_used: int = 0


def build_messages(message: str, history: List[HistoryMessage], severity: int) -> list:
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.format(
                resources=crisis_detector.format_resources(), today=date.today().isoformat()
            ),
        }
    ]
    if severity >= 4:
        messages.append({"role": "system", "content": CAREFUL_NOTE.format(severity=severity)})
    messages.extend(m.model_dump() for m in history[-settings.MAX_HISTORY_MESSAGES :])
    messages.append({"role": "user", "content": message})
    return messages


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # 1. Crisis check first - works even if the AI is down or not configured.
    is_crisis, severity, crisis_msg, _ = crisis_detector.detect(request.message)
    if is_crisis:
        return ChatResponse(response=crisis_msg, crisis_flag=True, severity=severity)

    # 2. AI reply.
    client = get_client()
    try:
        result = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_MAIN,
            messages=build_messages(request.message, request.history, severity),
            temperature=settings.OPENAI_TEMPERATURE_EMPATHY,
            max_tokens=500,
        )
    except Exception:
        logger.exception("AI request failed")
        raise HTTPException(status_code=502, detail="Robin couldn't reply right now. Please try again.")

    return ChatResponse(
        response=result.choices[0].message.content or "",
        severity=severity,
        tokens_used=getattr(result.usage, "total_tokens", 0) or 0,
    )


@router.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket):
    """Streaming chat. Send {"message": "...", "history": [...]}, receive chunks then {"type": "done"}."""
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                request = ChatRequest(**json.loads(raw))
            except Exception:
                await websocket.send_json({"type": "error", "error": "Invalid message format."})
                continue

            is_crisis, severity, crisis_msg, _ = crisis_detector.detect(request.message)
            if is_crisis:
                await websocket.send_json(
                    {"type": "crisis", "response": crisis_msg, "crisis_flag": True, "severity": severity}
                )
                continue

            if not settings.OPENAI_API_KEY:
                await websocket.send_json({"type": "error", "error": "Robin's AI is not configured."})
                continue

            try:
                stream = await get_client().chat.completions.create(
                    model=settings.OPENAI_MODEL_MAIN,
                    messages=build_messages(request.message, request.history, severity),
                    temperature=settings.OPENAI_TEMPERATURE_EMPATHY,
                    stream=True,
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        await websocket.send_json({"type": "chunk", "response": chunk.choices[0].delta.content})
                await websocket.send_json({"type": "done"})
            except Exception:
                logger.exception("AI stream failed")
                await websocket.send_json({"type": "error", "error": "Robin couldn't reply right now."})
    except WebSocketDisconnect:
        pass
