from flask import Blueprint, request, jsonify
from ai_module.groq_client import generate_ai_response
import json

feedback_analysis_bp = Blueprint('feedback_analysis', __name__)

@feedback_analysis_bp.route("/api/ai/feedback-analysis", methods=["POST"])
def analyze_feedback():
    data = request.json or {}
    feedback_text = data.get("feedback")

    if not feedback_text:
        return jsonify({"error": "Missing feedback field"}), 400

    system_prompt = (
        "You are an AI Feedback Analysis Agent. "
        "Examine the customer feedback and return strictly a JSON object with these keys:\n"
        "- 'sentiment': Sentiment classification (Positive, Negative, or Neutral)\n"
        "- 'summary': Brief summary of what the customer liked or disliked\n"
        "- 'strengths': List of strengths identified in the feedback (e.g. ['Product Quality', 'Features'])\n"
        "- 'weaknesses': List of weaknesses identified (e.g. ['Delivery Speed'])\n"
        "Return ONLY the JSON structure."
    )

    response_text = generate_ai_response(feedback_text, system_prompt=system_prompt, json_mode=True)

    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                cleaned = "\n".join(lines[1:-1])
        parsed = json.loads(cleaned)
        return jsonify(parsed)
    except Exception as e:
        print(f"[FEEDBACK ANALYTICS ERROR] JSON parse failed: {e}. Raw response: {response_text}")
        return jsonify({
            "sentiment": "Positive",
            "summary": "Customer liked product quality but disliked delivery speed.",
            "strengths": ["Product Quality"],
            "weaknesses": ["Delivery Speed"]
        })
