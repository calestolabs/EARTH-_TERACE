
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

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

if not FIREBASE_PROJECT_ID:
    raise RuntimeError("FIREBASE_PROJECT_ID is missing from .env")

# Firebase Admin Initialization

if not firebase_admin._apps:
    firebase_admin.initialize_app(
        credentials.ApplicationDefault(),
        {"projectId": FIREBASE_PROJECT_ID},
    )

bearer_scheme = HTTPBearer(auto_error=False)


def verify_firebase_user(
    authorization: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> str:
    """Verify Firebase ID token and return trusted Firebase UID."""

    if authorization is None:
        if os.getenv("RESULTS_MODE", "demo") == "demo":
            return "demo-user"
        raise HTTPException(
            status_code=401,
            detail="Firebase authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.credentials
    if os.getenv("RESULTS_MODE", "demo") == "demo" and token in ("demo-token", "demo"):
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

    except (ValueError, firebase_admin.exceptions.FirebaseError):
        if os.getenv("RESULTS_MODE", "demo") == "demo":
            return "demo-user"
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired Firebase ID token",
            headers={"WWW-Authenticate": "Bearer"},
        )

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

origins = [
    value.strip()
    for value in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if value.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

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

