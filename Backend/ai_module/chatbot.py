from flask import Blueprint, request, jsonify
from ai_module.groq_client import generate_ai_response_with_history

chatbot_bp = Blueprint('chatbot', __name__)

# Sales-focused system prompt that explicitly instructs the model to maintain context
SALESBOT_SYSTEM_PROMPT = """You are Salesbot, an expert universal virtual telesales representative and sales assistant. You can sell any product or service across all business domains (electronics, fashion, real estate, vehicles, construction materials, grocery, machinery, software, business services, etc.).

CRITICAL RULES — FOLLOW THESE STRICTLY:
1. ALWAYS identify the product or service category the user is interested in from their query (e.g., Real Estate, Vehicles, Electronics, Fashion, Construction/Hardware, Software, Services, etc.).
2. Adapt your line of questioning dynamically based on the category. Ask category-specific questions.
   - For Real Estate: Ask about preferred location, size/area, budget, and purpose (residential/commercial/agriculture).
   - For Vehicles: Ask about budget, usage, fuel type, and brand preference.
   - For Construction/Hardware: Ask about required quantity, construction type, preferred brand, and budget.
   - For Electronics: Ask about usage, budget, and preferred specifications.
   - For Fashion: Ask about size, style, occasion, and fit.
   - For other categories: Ask 2-3 most relevant qualifying questions.
3. NEVER assume every query is about electronics. Do not talk about electronics if the user asks about land, cement, cars, clothing, etc.
4. ALWAYS remember everything the user has told you in this conversation (budget, location, requirements, constraints).
5. NEVER ask for information the user has already provided in this conversation. Never ask the same question twice.
6. When the user provides follow-up answers, immediately combine ALL previously provided details and provide domain-specific recommendations.
7. Recommend 2-3 specific options with prices, specs/features, and key pros/cons. Use Indian Rupee (₹) where appropriate.
8. Be concise, professional, and helpful — like a knowledgeable, consultative salesperson."""


@chatbot_bp.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    data = request.json or {}
    query = data.get("query")
    # conversation_history: list of {role: "user"|"assistant", content: "..."}
    conversation_history = data.get("conversation_history", [])

    if not query:
        return jsonify({"error": "Missing query field"}), 400

    response = generate_ai_response_with_history(
        query,
        conversation_history=conversation_history,
        system_prompt=SALESBOT_SYSTEM_PROMPT
    )

    # Trigger background lead qualification if user details are provided
    user_details = data.get("user_details")
    if user_details:
        try:
            from main import process_lead_qualification_background
            import threading
            t = threading.Thread(
                target=process_lead_qualification_background,
                args=(query, user_details)
            )
            t.daemon = True
            t.start()
        except Exception as ex:
            print(f"[LEAD QUAL BG ERROR] {ex}")

    # Log conversation to database
    try:
        from database.db import db
        from models import Conversation
        user_id = user_details.get("user_id") if user_details else None
        user_obj = None
        if not user_id and user_details and user_details.get("email"):
            from models import User
            user_obj = User.query.filter_by(email=user_details.get("email")).first()
            if user_obj:
                user_id = user_obj.user_id
        elif user_id:
            from models import User
            user_obj = User.query.get(user_id)

        if user_obj:
            from datetime import datetime
            user_obj.last_activity_date = datetime.utcnow()

        new_conv = Conversation(
            user_id=user_id,
            user_message=query,
            ai_response=response
        )
        db.session.add(new_conv)
        db.session.commit()
    except Exception as ex:
        print(f"[CONVERSATION LOGGING ERROR] {ex}")

    return jsonify({"response": response})
