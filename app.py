# -*- coding: utf-8 -*-
"""
TanaCebu Bot 🌴 — A Facebook Messenger Chatbot for Cebu Tourism
Powered by Flask + Google Gemini API
"""

import os
import logging
import json
import requests
from google import genai
from google.genai import errors as genai_errors
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# ─── Load Environment Variables ────────────────────────────────────────────────
load_dotenv()

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN      = os.environ.get("VERIFY_TOKEN")
GEMINI_API_KEY    = os.environ.get("GEMINI_API_KEY")

# ─── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("tana_cebu.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ─── Gemini Setup ──────────────────────────────────────────────────────────────
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = (
    "You are TanaCebu 🌴, a fun and friendly Cebu tourism assistant. "
    "You help users find the best beaches, food, tourist spots, and travel tips in Cebu. "
    "Speak in a casual tone, mix English and Cebuano (Bisaya), and use emojis. "
    "Keep answers short, helpful, and engaging. "
    "Suggest real places like Bantayan Island, Moalboal, Kawasan Falls, Temple of Leah, "
    "and recommend local food like lechon, sutukil, and ngohiong. "
    "Always be warm, enthusiastic, and proud of Cebu's culture and beauty."
)

FALLBACK_MESSAGE = (
    "Hi! I'm TanaCebu 🌴 Ask me about beaches, food, or places to visit in Cebu!"
)

RATE_LIMIT_MESSAGE = (
    "Ambot oi! 😅 I'm getting too many questions right now. "
    "Try again in a minute, oks lang!"
)

INTRO_MESSAGE = (
    "Uy! 👋 I'm TanaCebu 🌴 — your kauban sa suroy!\n"
    "Ask me anything about beaches, food, or laag spots diri sa Cebu!"
)

# ─── Flask App ─────────────────────────────────────────────────────────────────
app = Flask(__name__)


# ─── Gemini Response Generator ─────────────────────────────────────────────────
def generate_response(user_message: str) -> str:
    """
    Send a user message to Gemini and return a tourism-focused reply.

    Args:
        user_message: The text received from the Messenger user.

    Returns:
        A string reply from Gemini, or the fallback message on failure.
    """
    # Try models in order; fall through on 429/503 to the next one
    MODELS = [
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-flash-lite-latest",
    ]
    for model_name in MODELS:
        try:
            response = gemini_client.models.generate_content(
                model=model_name,
                contents=user_message,
                config=genai.types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.85,
                    max_output_tokens=512,
                ),
            )
            reply = response.text.strip()
            logger.info("Gemini [%s] replied: %s", model_name, reply[:120])
            return reply
        except genai_errors.ClientError as exc:
            if exc.status_code == 429:
                logger.warning("Gemini [%s] rate limit — trying next model.", model_name)
                continue
            logger.error("Gemini [%s] client error: %s", model_name, exc)
            return FALLBACK_MESSAGE
        except genai_errors.ServerError as exc:
            logger.warning("Gemini [%s] server error (%s) — trying next model.", model_name, exc.status_code)
            continue
        except Exception as exc:
            logger.error("Gemini [%s] unexpected error: %s", model_name, exc)
            return FALLBACK_MESSAGE

    logger.error("All Gemini models failed or rate-limited.")
    return RATE_LIMIT_MESSAGE


# ─── Facebook Graph API Helpers ────────────────────────────────────────────────
GRAPH_API_URL = "https://graph.facebook.com/v19.0/me"


def send_action(recipient_id: str, action: str) -> None:
    """Send a sender action (e.g. 'typing_on') to the user."""
    payload = {
        "recipient": {"id": recipient_id},
        "sender_action": action,
    }
    try:
        requests.post(
            f"{GRAPH_API_URL}/messages",
            params={"access_token": PAGE_ACCESS_TOKEN},
            json=payload,
            timeout=5,
        )
    except Exception as exc:
        logger.warning("sender_action '%s' failed: %s", action, exc)


def send_quick_replies(recipient_id: str, text: str) -> None:
    """Send a message with Quick Reply buttons."""
    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "text": text,
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": "Beaches 🌊",
                    "payload": "BEACHES",
                },
                {
                    "content_type": "text",
                    "title": "Food 🍽️",
                    "payload": "FOOD",
                },
                {
                    "content_type": "text",
                    "title": "Spots 📍",
                    "payload": "SPOTS",
                },
            ],
        },
    }
    try:
        r = requests.post(
            f"{GRAPH_API_URL}/messages",
            params={"access_token": PAGE_ACCESS_TOKEN},
            json=payload,
            timeout=10,
        )
        r.raise_for_status()
        logger.info("Quick replies sent to %s", recipient_id)
    except Exception as exc:
        logger.error("send_quick_replies failed: %s", exc)


def send_message(recipient_id: str, text: str) -> None:
    """
    Send a plain text message to a Messenger user.

    Args:
        recipient_id: The Facebook user PSID.
        text:         The message content to send.
    """
    # Facebook limits messages to 2000 characters; split if needed
    chunks = [text[i : i + 1999] for i in range(0, len(text), 1999)]
    for chunk in chunks:
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": chunk},
        }
        try:
            r = requests.post(
                f"{GRAPH_API_URL}/messages",
                params={"access_token": PAGE_ACCESS_TOKEN},
                json=payload,
                timeout=10,
            )
            r.raise_for_status()
            logger.info("Message sent to %s: %s…", recipient_id, chunk[:60])
        except Exception as exc:
            logger.error("send_message failed for %s: %s", recipient_id, exc)


# ─── Webhook Routes ────────────────────────────────────────────────────────────
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Handle Facebook's webhook verification challenge.

    Facebook sends a GET request with hub.mode, hub.challenge,
    and hub.verify_token. We echo back hub.challenge on success.
    """
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    logger.info("Webhook verification attempt — mode: %s", mode)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("✅ Webhook verified successfully.")
        return challenge, 200

    logger.warning("❌ Webhook verification failed — token mismatch.")
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def handle_messages():
    """
    Receive and process incoming Messenger webhook events.

    Handles:
    - Standard text messages
    - Quick reply payloads (BEACHES, FOOD, SPOTS)
    - Postback events
    """
    data = request.get_json(silent=True)

    if not data:
        return "Bad Request", 400

    logger.info("Incoming webhook payload: %s", json.dumps(data)[:300])

    if data.get("object") != "page":
        return "Not a page event", 404

    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):
            sender_id = event["sender"]["id"]

            # ── Postback (e.g. Get Started button) ────────────────────────────
            if "postback" in event:
                payload = event["postback"].get("payload", "")
                logger.info("Postback from %s: %s", sender_id, payload)
                _handle_postback(sender_id, payload)
                continue

            # ── Text / Quick Reply message ─────────────────────────────────────
            if "message" in event:
                message = event["message"]

                # Quick reply shortcut
                if "quick_reply" in message:
                    qr_payload = message["quick_reply"]["payload"]
                    logger.info("Quick reply from %s: %s", sender_id, qr_payload)
                    _handle_quick_reply(sender_id, qr_payload)
                    continue

                user_text = message.get("text", "").strip()
                if not user_text:
                    continue

                logger.info("Message from %s: %s", sender_id, user_text)

                # Typing indicator on
                send_action(sender_id, "typing_on")

                # Generate and send reply
                reply = generate_response(user_text)
                send_message(sender_id, reply)

                # Typing indicator off
                send_action(sender_id, "typing_off")

    return "EVENT_RECEIVED", 200


# ─── Quick Reply & Postback Handlers ──────────────────────────────────────────
def _handle_quick_reply(sender_id: str, payload: str) -> None:
    """Route quick reply payloads to pre-built responses."""
    prompts = {
        "BEACHES": "List the top beaches in Cebu with short descriptions.",
        "FOOD":    "What are the must-try foods in Cebu? Give me a quick list.",
        "SPOTS":   "Give me the top tourist spots in Cebu with tips.",
    }
    user_prompt = prompts.get(payload, payload)
    send_action(sender_id, "typing_on")
    reply = generate_response(user_prompt)
    send_message(sender_id, reply)
    send_action(sender_id, "typing_off")


def _handle_postback(sender_id: str, payload: str) -> None:
    """Handle button postbacks such as the Get Started button."""
    if payload == "GET_STARTED":
        send_quick_replies(sender_id, INTRO_MESSAGE)
    else:
        send_action(sender_id, "typing_on")
        reply = generate_response(payload)
        send_message(sender_id, reply)
        send_action(sender_id, "typing_off")


# ─── Health Check ──────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def health_check():
    """Simple health-check endpoint."""
    return jsonify({"status": "ok", "bot": "TanaCebu 🌴", "version": "1.0.0"}), 200


# ─── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    missing = [v for v in ("PAGE_ACCESS_TOKEN", "VERIFY_TOKEN", "GEMINI_API_KEY") if not os.environ.get(v)]
    if missing:
        logger.warning("⚠️  Missing environment variables: %s", ", ".join(missing))

    port = int(os.environ.get("PORT", 5000))
    logger.info("🌴 TanaCebu Bot starting on port %d …", port)
    app.run(host="0.0.0.0", port=port, debug=False)
