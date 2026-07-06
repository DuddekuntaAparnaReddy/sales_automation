from flask import Blueprint, request, jsonify
from ai_module.groq_client import generate_ai_response
import json

campaign_generator_bp = Blueprint('campaign_generator', __name__)


def generate_campaign_content(product_name, offer_details, campaign_type="Promotional",
                               target_audience="General", discount=""):
    """
    Standalone function called internally (from main.py) or via API.
    Returns a dict with keys: title, subject, body, cta
    """
    prompt = (
        f"Generate a promotional marketing campaign for the following:\n"
        f"Product: {product_name}\n"
        f"Campaign Type: {campaign_type}\n"
        f"Offer/Discount Details: {offer_details}\n"
        f"Discount Percentage: {discount}\n"
        f"Target Audience: {target_audience}\n\n"
        f"Return ONLY a JSON object with these exact keys:\n"
        f"- 'title': A creative, catchy campaign title (max 10 words)\n"
        f"- 'subject': An engaging email subject line that creates urgency\n"
        f"- 'body': A 3-paragraph persuasive promotional email body with greeting, offer details, and urgency/CTA hint\n"
        f"- 'cta': A short call-to-action button text (2-4 words, e.g. 'Shop Now', 'Claim Offer')\n"
    )

    system_prompt = (
        "You are an expert Marketing Copywriter specialising in promotional campaigns. "
        "Your goal is to generate compelling, conversion-focused marketing content. "
        "Always tailor your language to the specified target audience. "
        "Return ONLY a valid JSON object — no explanation, no markdown fences, no extra text."
    )

    response_text = generate_ai_response(prompt, system_prompt=system_prompt, json_mode=True)

    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            cleaned = "\n".join(lines[1:-1]) if lines[0].startswith("```") else cleaned
        parsed = json.loads(cleaned)
        # Ensure body is always a string
        raw_body = parsed.get("body", "")
        if isinstance(raw_body, dict):
            parsed["body"] = "\n\n".join(str(v) for v in raw_body.values() if v)
        elif not isinstance(raw_body, str):
            parsed["body"] = str(raw_body)
        return parsed

    except Exception as e:
        print(f"[CAMPAIGN GEN] JSON parse failed: {e}. Using fallback.")
        return {
            "title":   f"{product_name} Special Offer",
            "subject": f"Exclusive Deal: {offer_details} on {product_name}!",
            "body": (
                f"Dear Valued Customer,\n\n"
                f"We are thrilled to announce an exclusive promotional offer on {product_name}. "
                f"{'Save ' + discount + ' on your purchase!' if discount else offer_details}\n\n"
                f"This is a limited-time offer exclusively for our {target_audience} customers. "
                f"Don't miss this incredible opportunity to get the best deal on {product_name}.\n\n"
                f"Visit our platform today to take advantage of this special offer before it expires!"
            ),
            "cta": "Shop Now"
        }


@campaign_generator_bp.route("/api/ai/campaign", methods=["POST"])
def generate_campaign_api():
    """API endpoint for standalone AI campaign content generation."""
    data = request.json or {}
    product_name    = data.get("product_name", "")
    offer_details   = data.get("offer_details", data.get("offer", ""))
    campaign_type   = data.get("campaign_type", "Promotional")
    target_audience = data.get("target_audience", "General")
    discount        = data.get("discount", "")

    if not product_name:
        return jsonify({"error": "Missing product_name field"}), 400

    result = generate_campaign_content(
        product_name=product_name,
        offer_details=offer_details,
        campaign_type=campaign_type,
        target_audience=target_audience,
        discount=discount
    )
    return jsonify(result)
