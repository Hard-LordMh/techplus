import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "").strip()
    TARGET_PHONE_NUMBER = os.getenv("TARGET_PHONE_NUMBER", "").strip()
    ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "").strip()

    @classmethod
    def is_twilio_configured(cls) -> bool:
        return bool(cls.TWILIO_ACCOUNT_SID and cls.TWILIO_AUTH_TOKEN and cls.TWILIO_PHONE_NUMBER)

    @classmethod
    def is_elevenlabs_configured(cls) -> bool:
        return bool(cls.ELEVENLABS_API_KEY and cls.ELEVENLABS_AGENT_ID)

    @classmethod
    def get_status(cls):
        return {
            "elevenlabs_configured": cls.is_elevenlabs_configured(),
            "twilio_configured": cls.is_twilio_configured(),
            "agent_id_configured": bool(cls.ELEVENLABS_AGENT_ID),
            "target_phone_configured": bool(cls.TARGET_PHONE_NUMBER),
            "details": {
                "ELEVENLABS_API_KEY": "Configured" if cls.ELEVENLABS_API_KEY else "Missing",
                "TWILIO_ACCOUNT_SID": "Configured" if cls.TWILIO_ACCOUNT_SID else "Missing",
                "TWILIO_AUTH_TOKEN": "Configured" if cls.TWILIO_AUTH_TOKEN else "Missing",
                "TWILIO_PHONE_NUMBER": "Configured" if cls.TWILIO_PHONE_NUMBER else "Missing",
                "TARGET_PHONE_NUMBER": "Configured" if cls.TARGET_PHONE_NUMBER else "Missing",
                "ELEVENLABS_AGENT_ID": "Configured" if cls.ELEVENLABS_AGENT_ID else "Missing",
            }
        }
