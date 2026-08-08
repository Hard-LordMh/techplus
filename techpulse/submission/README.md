# MCP Mega Workshop Submission Guide - TechPulse

This folder serves as your workshop submission workspace. Below is a checklist of the required evidence you must capture to complete your submission.

## Short Project Description
**TechPulse** is an AI-powered voice agent that delivers concise, real-time technology updates (covering AI, Programming, and Cybersecurity) using ElevenLabs Conversational AI, orchestrated via a FastAPI backend, and dialed out via Twilio telephony. It includes a sleek dashboard UI to monitor status, place calls, view live news feeds, and review call histories.

---

## Required Submission Screenshots

### 1. ElevenLabs Agent Call History
*   **Suggested Filename:** `01-elevenlabs-call-history.png`
*   **What it Proves:** Verifies that your ElevenLabs Agent successfully processed the call, executed the system prompt (intro, briefing, and details request), and generated audio streams.
*   **Where to Capture:** Go to your **ElevenLabs Dashboard** > **Conversational AI** > Select your **TechPulse** agent > Click **Call History** or **Sessions** tab.
*   **Visual Evidence Check:** Should show a list of calls with status "Success", date, duration, and a transcription of the dialogue showing the agent asking: *"Hey, I've got some quick tech updates for you — should I go ahead?"*.

### 2. Twilio Active Phone Number
*   **Suggested Filename:** `02-twilio-active-number.png`
*   **What it Proves:** Proves that you configured and purchased a valid phone number via Twilio to host inbound and place outbound voice calls.
*   **Where to Capture:** Go to **Twilio Console** > **Develop** > **Phone Numbers** > **Manage** > **Active Numbers**.
*   **Visual Evidence Check:** Should clearly display your active Twilio phone number, showing its capabilities (Voice, SMS).

### 3. MCP / IDE Integration Screenshot
*   **Suggested Filename:** `03-mcp-tool-calls.png`
*   **What it Proves:** Proves that the `elevenlabs-mcp` server was integrated and running in your local editor environment, and that tools were successfully registered and invoked.
*   **Where to Capture:** Take a screenshot of your IDE showing the MCP settings panel or the chat interface executing ElevenLabs commands (e.g. asking the assistant to list ElevenLabs voices or text-to-speech tools).
*   **Visual Evidence Check:** The log panel or chat interface should show tool execution logs from the `elevenlabs` MCP server.
