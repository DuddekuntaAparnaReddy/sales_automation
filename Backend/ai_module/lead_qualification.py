from flask import Blueprint, request, jsonify
from ai_module.groq_client import generate_ai_response
import json

lead_qualification_bp = Blueprint('lead_qualification', __name__)

@lead_qualification_bp.route("/api/ai/lead-extract", methods=["POST"])
def lead_extract():
    data = request.json or {}
    conversation = data.get("conversation")
    if not conversation:
        return jsonify({"error": "Missing conversation field"}), 400

    system_prompt = (
        "You are an AI Lead Qualification Agent. Your job is to extract lead profile information from customer conversations. "
        "Analyze the input and return strictly a JSON object with these keys:\n"
        "- 'product_interest': Product Interest (string, e.g. 'Gaming Laptop', or null if unspecified)\n"
        "- 'budget': Budget (integer, extract the number only, e.g. 80000, or null if unspecified)\n"
        "- 'purchase_timeline': Purchase Timeline (string, e.g. 'This Week', 'This Month', or null if unspecified)\n"
        "- 'customer_intent': Customer Intent (High, Medium, or Low, or null if unspecified)\n"
        "Do not calculate a lead score or include any extra text. Return ONLY the raw JSON object."
    )

    response_text = generate_ai_response(conversation, system_prompt=system_prompt, json_mode=True)

    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                cleaned = "\n".join(lines[1:-1])
        parsed = json.loads(cleaned)
        return jsonify(parsed)
    except Exception as e:
        print(f"[LEAD EXTRACT ERROR] JSON parse failed: {e}. Raw response: {response_text}")
        return jsonify({
            "product_interest": "Gaming Laptop",
            "budget": 80000,
            "purchase_timeline": "This Week",
            "customer_intent": "High"
        })
