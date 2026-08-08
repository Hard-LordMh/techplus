import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List

from backend.config import Config
from backend.news import NewsManager
from backend.calls import CallManager, validate_phone_number

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("techpulse.main")

app = FastAPI(
    title="TechPulse AI Voice Agent API",
    description="Backend API for managing outbound Twilio calls and ElevenLabs AI Voice Agent for technology updates.",
    version="1.0.0"
)

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the dashboard origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class CallRequest(BaseModel):
    phone_number: str = Field(
        ..., 
        description="Target phone number in E.164 format (+[country][number]). Example: +1234567890"
    )

# Endpoints
@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    """Returns the API health status and current server time."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app": "TechPulse API"
    }

@app.get("/api/config/status")
def config_status() -> Dict[str, Any]:
    """
    Exposes configuration readiness indicators.
    Never exposes actual keys or secrets.
    """
    return Config.get_status()

@app.post("/api/call", status_code=status.HTTP_201_CREATED)
def make_call(request: CallRequest) -> Dict[str, Any]:
    """
    Validates configuration and phone number, then triggers an outbound call.
    Runs in Mock Mode if Twilio or ElevenLabs is not fully configured.
    """
    phone_number = request.phone_number.strip()
    
    # 1. Validate phone number format
    if not validate_phone_number(phone_number):
        logger.warning(f"Rejected call request: Invalid E.164 format for '{phone_number}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format. It must be E.164 format starting with '+' followed by country code and numbers (e.g. +1234567890)."
        )

    # 2. Trigger call (Live or Mock fallback)
    try:
        call_details = CallManager.make_outbound_call(phone_number)
        return {
            "success": True,
            "message": "Call initiated successfully." if not call_details["is_mock"] else "Call initiated in Mock Mode.",
            "call": call_details
        }
    except ValueError as ve:
        logger.error(f"Value error triggering call: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Failed to initiate call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate call: {str(e)}"
        )

@app.post("/api/call/test", status_code=status.HTTP_201_CREATED)
def make_test_call() -> Dict[str, Any]:
    """
    Triggers an outbound call to the target phone number configured in `.env`.
    Fails if TARGET_PHONE_NUMBER is not set.
    """
    target = Config.TARGET_PHONE_NUMBER
    if not target:
        logger.warning("Test call requested but TARGET_PHONE_NUMBER is not configured in environment.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TARGET_PHONE_NUMBER is not configured in the backend environment (.env)."
        )
    
    try:
        call_details = CallManager.make_outbound_call(target)
        return {
            "success": True,
            "message": "Test call initiated successfully." if not call_details["is_mock"] else "Test call initiated in Mock Mode.",
            "call": call_details
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/calls")
def get_calls() -> List[Dict[str, Any]]:
    """Retrieves list of recent outbound call history."""
    try:
        return CallManager.get_recent_calls()
    except Exception as e:
        logger.error(f"Failed to fetch calls: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve call history: {str(e)}"
        )

@app.get("/api/news")
def get_news() -> Dict[str, Dict[str, str]]:
    """Returns the structured technology news items."""
    return NewsManager.get_all_news()

@app.get("/api/news/briefing")
def get_news_briefing(use_fallback: bool = False) -> Dict[str, str]:
    """
    Returns the compiled voice briefing.
    Supports use_fallback query param to force the ElevenLabs fallback text.
    """
    briefing = NewsManager.get_compiled_briefing(use_fallback=use_fallback)
    return {
        "briefing": briefing,
        "mode": "fallback" if use_fallback else "live_news"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
