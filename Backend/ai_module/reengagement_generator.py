from flask import Blueprint, request, jsonify
from ai_module.groq_client import generate_ai_response
import json

reengagement_generator_bp = Blueprint('reengagement_generator', __name__)

@reengagement_generator_bp.route("/api/ai/reengagement", methods=["POST"])
def generate_reengagement():
    data = request.json or {}
    customer_name = data.get("customer_name")
    previous_interest = data.get("previous_interest")
    last_interaction = data.get("last_interaction")

    if not customer_name:
        return jsonify({"error": "Missing customer_name field"}), 400

    prompt = (
        f"Generate a re-engagement follow-up message for:\n"
        f"Customer Name: {customer_name}\n"
        f"Previous Interest: {previous_interest}\n"
        f"Last Interaction: {last_interaction}\n"
    )

    system_prompt = (
        "You are an AI Customer Re-engagement Agent. "
        "Create a personalized follow-up email/reminder layout returned strictly in JSON format:\n"
        "- 'subject': High-open-rate subject line re-engaging the user\n"
        "- 'body': A warm, personalized re-engagement follow-up email/message referencing their previous interest and offering assistance\n"
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
        print(f"[REENGAGEMENT GEN ERROR] JSON parse failed: {e}. Raw response: {response_text}")
        return jsonify({
            "subject": f"We Miss You, {customer_name}!",
            "body": f"Hi {customer_name},\n\nIt has been a while since we last spoke (last active: {last_interaction}). We noticed you had interest in '{previous_interest}' and wanted to see if we can help you with anything else today!\n\nBest regards,\nSalesbot Team"
        })
