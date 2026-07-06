from flask import Blueprint, request, jsonify
from ai_module.groq_client import generate_ai_response
import json

email_generator_bp = Blueprint('email_generator', __name__)

@email_generator_bp.route("/api/ai/email", methods=["POST"])
def generate_email():
    data = request.json or {}
    email_type = data.get("email_type")
    context = data.get("context", "")

    if not email_type:
        return jsonify({"error": "Missing email_type field"}), 400

    prompt = (
        f"Generate email content for:\n"
        f"Email Type: {email_type}\n"
        f"Context details: {context}\n"
    )

    system_prompt = (
        "You are an Email Content Generator. Create email content returned strictly in JSON format:\n"
        "- 'subject': Captivating email subject line\n"
        "- 'body': Well-formatted email body content matching the request type and context details\n"
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
        print(f"[EMAIL GEN ERROR] JSON parse failed: {e}. Raw response: {response_text}")
        return jsonify({
            "subject": f"Update regarding your {email_type}",
            "body": f"Hi there,\n\nHere is your custom content for {email_type}.\n\nContext details:\n{context}\n\nSincerely,\nSalesbot Team"
        })
