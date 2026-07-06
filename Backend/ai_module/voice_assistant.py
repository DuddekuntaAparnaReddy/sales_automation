from flask import Blueprint, request, jsonify
from ai_module.groq_client import generate_ai_response

voice_assistant_bp = Blueprint('voice_assistant', __name__)

@voice_assistant_bp.route("/api/ai/voice-chat", methods=["POST"])
def voice_chat():
    data = request.json or {}
    query = data.get("query")
    if not query:
        return jsonify({"error": "Missing query field"}), 400

    system_prompt = (
        "You are an expert AI Telephony Voice Assistant for Salesbot. "
        "The customer is speaking to you directly. "
        "Provide professional, helpful, and extremely concise responses (max 2 sentences/30 words) suitable for real-time text-to-speech reading. "
        "Do NOT use markdown bold/italic tags, emojis, lists, or bullets. Keep the text simple and clean."
    )

    response = generate_ai_response(query, system_prompt=system_prompt, json_mode=False)

    # Trigger background lead qualification if user details are provided
    user_details = data.get("user_details")
    if user_details:
        from main import process_lead_qualification_background
        import threading
        t = threading.Thread(target=process_lead_qualification_background, args=(query, user_details))
        t.daemon = True
        t.start()

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
