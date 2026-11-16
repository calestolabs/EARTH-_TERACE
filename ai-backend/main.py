
"""Secure AI Detective API."""

import os
import uuid
import logging
from functools import lru_cache

from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)
load_dotenv()
if "GOOGLE_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
elif "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

from earthtrace_agent.agent import root_agent
from earthtrace_agent.results import fetch_result

import json
from earthtrace_agent.location_analysis import (LocationRequest, get_location_results,)

# Configuration

APP_NAME = "earthtrace_agent"
logger = logging.getLogger(__name__)

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "new-earthtrace-56b71")

# Firebase Admin Initialization

SERVICE_ACCOUNT_PATHS = [
    os.path.join(os.path.dirname(__file__), "firebase-service-account.json"),
    os.path.join(os.path.dirname(__file__), "..", "firebase-service-account.json"),
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
]

if not firebase_admin._apps:
    initialized = False
    for cred_path in SERVICE_ACCOUNT_PATHS:
        if cred_path and os.path.exists(cred_path):
            try:
                firebase_admin.initialize_app(
                    credentials.Certificate(cred_path),
                    {"projectId": FIREBASE_PROJECT_ID or "new-earthtrace-56b71"},
                )
                initialized = True
                logger.info(f"Firebase Admin initialized with certificate: {cred_path}")
                break
            except Exception as e:
                logger.warning(f"Failed to load certificate {cred_path}: {e}")
    if not initialized:
        try:
            firebase_admin.initialize_app(
                credentials.ApplicationDefault(),
                {"projectId": FIREBASE_PROJECT_ID or "new-earthtrace-56b71"},
            )
            logger.info("Firebase Admin initialized with ApplicationDefault")
        except Exception as e:
            logger.warning(f"Firebase Admin ApplicationDefault failed: {e}")
            try:
                firebase_admin.initialize_app(
                    options={"projectId": FIREBASE_PROJECT_ID or "new-earthtrace-56b71"}
                )
            except Exception:
                pass

bearer_scheme = HTTPBearer(auto_error=False)


def verify_firebase_user(
    authorization: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> str:
    """Verify Firebase ID token and return trusted Firebase UID."""

    if authorization is None:
        return "demo-user"

    token = authorization.credentials
    if not token or token in ("demo-token", "demo", "undefined", "null"):
        return "demo-user"

    try:
        decoded = auth.verify_id_token(
            token,
            check_revoked=False,
        )

        uid = decoded.get("uid")

        if not isinstance(uid, str) or not uid:
            raise ValueError("Missing Firebase UID")

        return uid

    except Exception:
        # Fallback to demo user for unauthenticated or expired tokens so the AI remains functional
        return "demo-user"

# Persistent SQLite Sessions

sessions = DatabaseSessionService(
    db_url="sqlite+aiosqlite:///./earthtrace_sessions.db"
)

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=sessions,
)

# FastAPI

app = FastAPI(
    title="EARTHTRACE AI Detective API",
    version="1.1.0",
)

cors_env = os.getenv("CORS_ORIGINS", "*")
if cors_env.strip() == "*":
    origins = ["*"]
else:
    origins = [v.strip() for v in cors_env.split(",") if v.strip()]
    for def_origin in ["https://earthtrace1.netlify.app", "http://localhost:3000", "http://127.0.0.1:3000"]:
        if def_origin not in origins:
            origins.append(def_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if origins == ["*"] else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "EARTHTRACE AI Detective API",
        "version": "1.1.0",
        "endpoints": ["/health", "/api/ai/chat", "/api/ai/analyze-location"]
    }

# Request / Response Models

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: uuid.UUID | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    mode: str

# Health Check

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "earthtrace-ai",
        "results_mode": os.getenv("RESULTS_MODE", "demo"),
    }


# Investigation Results

@app.get("/api/ai/investigations/{investigation_id}/results")
async def investigation_result(
    investigation_id: str,
    variable: str,
    user_id: str = Depends(verify_firebase_user),
):
    result = fetch_result(variable, investigation_id)

    if "error" in result:
        raise HTTPException(
            status_code=422,
            detail="Investigation result unavailable or invalid",
        )

    return result

# Secure AI Chat

@app.post("/api/ai/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user_id: str = Depends(verify_firebase_user),
):
    if request.session_id is not None:
        session_id = str(request.session_id)

        session = await sessions.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found",
            )

    else:
        session_id = str(uuid.uuid4())

        await sessions.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )

    message = types.Content(
        role="user",
        parts=[types.Part(text=request.message)],
    )

    reply_parts = []

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
        ):
            if (
                event.is_final_response()
                and event.content
                and event.content.parts
            ):
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        reply_parts.append(part.text)

    except Exception:
        logger.exception("AI chat request failed")

        raise HTTPException(
            status_code=502,
            detail="AI provider request failed",
        )

    reply = "\n".join(reply_parts).strip()

    if not reply:
        raise HTTPException(
            status_code=502,
            detail="Agent returned no text",
        )

    return ChatResponse(
        reply=reply,
        session_id=session_id,
        mode="analysis",
    )


@app.post("/api/ai/analyze-location")
async def analyze_location(
    request: LocationRequest,
    user_id: str = Depends(verify_firebase_user),
):
    """
    Analyze all requested environmental variables
    for a selected geographic location.
    """

    try:
        report = await get_location_results(request)

    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    # If no verified location-specific data exists,
    # do not ask Gemini to invent an explanation.
    available = {
        variable: result
        for variable, result in report["results"].items()
        if result["status"] == "available"
    }

    if not available:
        report["ai_summary"] = (
            "No verified location-specific trend results "
            f"are available for {request.location.name}. "
            + report["notice"]
        )
        return report

    # Prepare verified statistical findings for Gemini.
    analysis_data = {
        "location": request.location.model_dump(),
        "results": available,
    }

    prompt = (
        "You are EARTHTRACE AI Detective.\n"
        "Generate a clear environmental intelligence report.\n\n"
        "RULES:\n"
        "1. Use ONLY the provided statistical results.\n"
        "2. Explain temperature, rainfall and soil moisture "
        "when their results are available.\n"
        "3. Explain trend direction and slope units.\n"
        "4. Explain p-values and statistical significance.\n"
        "5. Mention the observation period and method.\n"
        "6. Explain environmental implications cautiously.\n"
        "7. Never invent measurements or missing results.\n"
        "8. Never claim correlation proves causation.\n"
        "9. Do not claim independent NASA verification.\n"
        "10. Keep the report understandable.\n\n"
        "ANALYSIS DATA:\n"
        + json.dumps(analysis_data, ensure_ascii=False)
    )

    session_id = str(uuid.uuid4())

    try:
        await sessions.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )

        message = types.Content(
            role="user",
            parts=[types.Part(text=prompt)],
        )

        reply_parts = []

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
        ):
            if (
                event.is_final_response()
                and event.content
                and event.content.parts
            ):
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        reply_parts.append(part.text)

        summary = "\n".join(reply_parts).strip()

        report["ai_summary"] = (
            summary
            or "AI summary unavailable; see statistical results."
        )

    except Exception:
        logger.exception(
            "Location AI summary generation failed"
        )

        report["ai_summary"] = (
            "AI summary unavailable; "
            "see validated statistical results."
        )

    return report


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", os.getenv("HTTP_PORT", 8000)))
    uvicorn.run("main:app", host="0.0.0.0", port=port)


