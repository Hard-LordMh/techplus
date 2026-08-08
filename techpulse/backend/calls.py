import re
import uuid
import logging
import asyncio
import requests
from datetime import datetime
from typing import Dict, Any, List
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from backend.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("techpulse.calls")

# In-memory database for mock calls
MOCK_CALLS_DB: Dict[str, Dict[str, Any]] = {}

def validate_phone_number(phone_number: str) -> bool:
    """
    Validates that a phone number is in E.164 format (+[country code][number]).
    Example: +1234567890
    """
    if not phone_number:
        return False
    # E.164 format validation regex
    pattern = r"^\+[1-9]\d{1,14}$"
    return bool(re.match(pattern, phone_number))

async def simulate_call_lifecycle(call_sid: str):
    """
    Simulates call status transitions for Mock Mode in the background:
    queued -> ringing -> in-progress -> completed
    """
    try:
        await asyncio.sleep(2)
        if call_sid in MOCK_CALLS_DB:
            MOCK_CALLS_DB[call_sid]["status"] = "ringing"
            logger.info(f"Mock Call {call_sid}: ringing")

        await asyncio.sleep(3)
        if call_sid in MOCK_CALLS_DB:
            MOCK_CALLS_DB[call_sid]["status"] = "in-progress"
            logger.info(f"Mock Call {call_sid}: in-progress")

        # Simulate call duration
        for seconds in range(1, 11):
            await asyncio.sleep(1)
            if call_sid in MOCK_CALLS_DB:
                MOCK_CALLS_DB[call_sid]["duration"] = seconds

        if call_sid in MOCK_CALLS_DB:
            MOCK_CALLS_DB[call_sid]["status"] = "completed"
            logger.info(f"Mock Call {call_sid}: completed")
    except Exception as e:
        logger.error(f"Error in mock call simulation: {str(e)}")

class CallManager:
    @classmethod
    def get_elevenlabs_twiml(cls, from_number: str, to_number: str) -> str:
        """
        Calls ElevenLabs API to register a call and get TwiML for Twilio.
        """
        if not Config.ELEVENLABS_API_KEY or not Config.ELEVENLABS_AGENT_ID:
            raise ValueError("ElevenLabs API Key or Agent ID not configured")

        url = "https://api.elevenlabs.io/v1/convai/twilio/register-call"
        headers = {
            "xi-api-key": Config.ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "agent_id": Config.ELEVENLABS_AGENT_ID,
            "from_number": from_number,
            "to_number": to_number
        }

        logger.info(f"Registering Twilio call with ElevenLabs Agent ID: {Config.ELEVENLABS_AGENT_ID}")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        logger.info(f"ElevenLabs response status: {response.status_code}, content: {response.text}")
        
        if response.status_code != 200:
            raise Exception(f"ElevenLabs API failed with status {response.status_code}: {response.text}")
            
        # The ElevenLabs API returns the raw TwiML XML document directly.
        twiml = response.text.strip()
        
        # Fallback to JSON parsing in case the API format ever returns JSON in future environments.
        if twiml and not (twiml.startswith("<?xml") or twiml.startswith("<Response")):
            try:
                data = response.json()
                twiml = data.get("twiml", twiml)
            except Exception:
                pass
                
        if not twiml:
            raise Exception("No TwiML returned from ElevenLabs register-call API")

        return twiml

    @classmethod
    def make_outbound_call(cls, target_phone: str) -> Dict[str, Any]:
        """
        Triggers an outbound call to the target phone number.
        Uses real Twilio + ElevenLabs APIs if configured, otherwise falls back to Mock Mode.
        """
        if not validate_phone_number(target_phone):
            raise ValueError(f"Invalid phone number format: '{target_phone}'. Must be in E.164 format (e.g. +1234567890).")

        # Determine mode
        use_live = Config.is_twilio_configured() and Config.is_elevenlabs_configured()

        if use_live:
            try:
                # 1. Register with ElevenLabs and get TwiML
                twiml_content = cls.get_elevenlabs_twiml(Config.TWILIO_PHONE_NUMBER, target_phone)

                # 2. Trigger outbound call using Twilio SDK
                twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
                call = twilio_client.calls.create(
                    twiml=twiml_content,
                    to=target_phone,
                    from_=Config.TWILIO_PHONE_NUMBER
                )

                logger.info(f"Outbound call successfully initiated via Twilio. SID: {call.sid}")
                return {
                    "sid": call.sid,
                    "to": target_phone,
                    "from": Config.TWILIO_PHONE_NUMBER,
                    "status": call.status,
                    "date_created": datetime.utcnow().isoformat(),
                    "duration": 0,
                    "is_mock": False
                }

            except TwilioRestException as te:
                logger.error(f"Twilio REST Error: {str(te)}")
                raise Exception(f"Twilio telephony error: {te.msg}")
            except Exception as e:
                logger.error(f"Live outbound call failed: {str(e)}")
                raise e
        else:
            # Fallback to Mock Mode
            mock_sid = f"CA{uuid.uuid4().hex}"
            now_iso = datetime.utcnow().isoformat()
            
            call_record = {
                "sid": mock_sid,
                "to": target_phone,
                "from": Config.TWILIO_PHONE_NUMBER or "+15017122661 (Mock)",
                "status": "queued",
                "date_created": now_iso,
                "duration": 0,
                "is_mock": True
            }
            MOCK_CALLS_DB[mock_sid] = call_record

            # Trigger background task to cycle call status
            asyncio.create_task(simulate_call_lifecycle(mock_sid))
            logger.info(f"Simulating outbound call in Mock Mode. SID: {mock_sid}")
            
            return call_record

    @classmethod
    def get_recent_calls(cls) -> List[Dict[str, Any]]:
        """
        Retrieves recent calls. 
        Combines Twilio call history (if configured) with local mock call history.
        """
        results = []

        # Get mock calls sorted by date created desc
        mock_calls = list(MOCK_CALLS_DB.values())
        mock_calls.sort(key=lambda x: x["date_created"], reverse=True)
        results.extend(mock_calls)

        # Retrieve real calls if Twilio configured
        if Config.is_twilio_configured():
            try:
                twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
                real_calls = twilio_client.calls.list(limit=10)
                for call in real_calls:
                    results.append({
                        "sid": call.sid,
                        "to": call.to,
                        "from": getattr(call, "from_", getattr(call, "_from", "")),
                        "status": call.status,
                        "date_created": call.date_created.isoformat() if call.date_created else "",
                        "duration": int(call.duration) if call.duration else 0,
                        "is_mock": False
                    })
            except Exception as e:
                logger.error(f"Failed to fetch real Twilio calls: {str(e)}")

        # Final sort by date created
        results.sort(key=lambda x: x["date_created"], reverse=True)
        return results[:20] # limit to 20 recent calls

    @classmethod
    def get_call_status(cls, call_sid: str) -> Dict[str, Any]:
        """
        Retrieves status of a specific call.
        """
        # Check mock database first
        if call_sid in MOCK_CALLS_DB:
            return MOCK_CALLS_DB[call_sid]

        # Fetch from Twilio
        if Config.is_twilio_configured():
            try:
                twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
                call = twilio_client.calls(call_sid).fetch()
                return {
                    "sid": call.sid,
                    "to": call.to,
                    "from": getattr(call, "from_", getattr(call, "_from", "")),
                    "status": call.status,
                    "date_created": call.date_created.isoformat() if call.date_created else "",
                    "duration": int(call.duration) if call.duration else 0,
                    "is_mock": False
                }
            except Exception as e:
                logger.error(f"Failed to fetch Twilio call status: {str(e)}")
                raise Exception(f"Failed to retrieve call details: {str(e)}")

        raise ValueError(f"Call with SID {call_sid} not found")
