from flask import Blueprint, request, jsonify
from ai_module.groq_client import generate_ai_response
import json

invitation_generator_bp = Blueprint('invitation_generator', __name__)

@invitation_generator_bp.route("/api/ai/event-invitation", methods=["POST"])
def generate_invitation():
    data = request.json or {}
    event_name = data.get("event_name")
    event_date = data.get("event_date")
    venue = data.get("venue")
    description = data.get("description")

    if not event_name:
        return jsonify({"error": "Missing event_name field"}), 400

    prompt = (
        f"Generate a customized event invitation for:\n"
        f"Event Name: {event_name}\n"
        f"Event Date: {event_date}\n"
        f"Venue: {venue}\n"
        f"Description: {description}\n"
    )

    system_prompt = (
        "You are an Event Coordinator and Copywriter. Create an email invitation returned strictly in JSON format:\n"
        "- 'subject': Engaging invitation subject line\n"
        "- 'body': Personalized event invitation body content displaying the venue, date, and event description\n"
        "Return ONLY the JSON structure."
    )

    response_text = generate_ai_response(prompt, system_prompt=system_prompt, json_mode=True)

    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                cleaned = "\n".join(lines[1:-1])
        parsed = json.loads(cleaned)
        return jsonify(parsed)
    except Exception as e:
        print(f"[INVITATION GEN ERROR] JSON parse failed: {e}. Raw response: {response_text}")
        return jsonify({
            "subject": f"You are Invited to {event_name}!",
            "body": f"Hi there,\n\nWe are excited to invite you to our event: '{event_name}' on {event_date} at {venue}.\n\nDetails: {description}\n\nWe look forward to seeing you there!"
        })

@invitation_generator_bp.route("/api/ai/registration-confirmation", methods=["POST"])
def generate_registration_confirmation():
    data = request.json or {}
    event_name = data.get("event_name")
    event_date = data.get("event_date")
    time = data.get("time")
    venue = data.get("venue")
    user_name = data.get("full_name")

    if not event_name or not user_name:
        return jsonify({"error": "Missing event_name or full_name field"}), 400

    prompt = (
        f"Generate a registration confirmation email for:\n"
        f"Recipient Name: {user_name}\n"
        f"Event Name: {event_name}\n"
        f"Event Date: {event_date}\n"
        f"Time: {time}\n"
        f"Venue: {venue}\n"
    )

    system_prompt = (
        "You are an Event Coordinator. Create a professional registration confirmation email returned strictly in JSON format:\n"
        "- 'subject': Clear confirmation subject line (e.g. 'Registration Confirmed: [Event Name]')\n"
        "- 'body': Warm, professional registration confirmation email body confirming their seat, summarizing the date, time, and venue, and thanking them.\n"
        "Return ONLY the JSON structure. Do not output anything else."
    )

    response_text = generate_ai_response(prompt, system_prompt=system_prompt, json_mode=True)

    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                cleaned = "\n".join(lines[1:-1])
        parsed = json.loads(cleaned)
        return jsonify(parsed)
    except Exception as e:
        print(f"[CONFIRMATION GEN ERROR] JSON parse failed: {e}. Raw response: {response_text}")
        return jsonify({
            "subject": f"Registration Confirmed: {event_name}",
            "body": f"Dear {user_name},\n\nThank you for registering for our event: '{event_name}' on {event_date} at {time} located at {venue}.\n\nYour registration is confirmed. We look forward to seeing you there!\n\nRegards,\nSales Team"
        })

@invitation_generator_bp.route("/api/ai/event-message", methods=["POST"])
def generate_message_invitation():
    data = request.json or {}
    event_name = data.get("event_name")
    event_date = data.get("event_date")
    venue = data.get("venue")
    time = data.get("time")
    description = data.get("description")

    if not event_name:
        return jsonify({"error": "Missing event_name field"}), 400

    prompt = (
        f"Generate a customized event invitation text message for:\n"
        f"Event Name: {event_name}\n"
        f"Event Date: {event_date}\n"
        f"Time: {time}\n"
        f"Venue: {venue}\n"
        f"Description: {description}\n"
    )

    system_prompt = (
        "You are an Event Coordinator and Copywriter. Create a short, highly engaging SMS/WhatsApp style event invitation returned strictly in JSON format:\n"
        "- 'body': A warm, concise text message invitation displaying the venue, date, time, and event description (with emojis, under 300 characters)\n"
        "Return ONLY the JSON structure. Do not output anything else."
    )

    response_text = generate_ai_response(prompt, system_prompt=system_prompt, json_mode=True)

    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                cleaned = "\n".join(lines[1:-1])
        parsed = json.loads(cleaned)
        return jsonify(parsed)
    except Exception as e:
        print(f"[INVITATION MSG GEN ERROR] JSON parse failed: {e}. Raw response: {response_text}")
        return jsonify({
            "body": f"Hi! You're invited to our upcoming event '{event_name}' on {event_date} at {time} at {venue}. Details: {description}. Don't miss out!"
        })

