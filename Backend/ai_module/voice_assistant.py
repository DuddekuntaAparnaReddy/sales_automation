from flask import Blueprint, request, jsonify
from ai_module.groq_client import generate_ai_response
from ai_module.stt_deepgram import transcribe_audio_bytes
from ai_module.tts_sarvam import synthesize_speech_sarvam

voice_assistant_bp = Blueprint('voice_assistant', __name__)

@voice_assistant_bp.route("/api/ai/voice-chat", methods=["POST"])
def voice_chat():
    data = request.json or {}
    query = data.get("query")
    if not query:
        return jsonify({"error": "Missing query field"}), 400

    system_prompt = (
        "You are an expert AI Voice Assistant for Salesbot. "
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


# --- DEEPGRAM STT ENDPOINT ---
@voice_assistant_bp.route("/api/voice/stt", methods=["POST"])
def deepgram_stt_route():
    try:
        audio_file = request.files.get("audio")
        mimetype = request.form.get("mimetype", "audio/wav")
        language = request.form.get("language", "en")
        
        if not audio_file:
            audio_bytes = request.data
        else:
            audio_bytes = audio_file.read()
            
        if not audio_bytes:
            return jsonify({"error": "No audio payload provided"}), 400
            
        res = transcribe_audio_bytes(audio_bytes, mimetype=mimetype, language=language)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e), "engine": "error"}), 500


# --- SARVAM AI TTS ENDPOINT ---
@voice_assistant_bp.route("/api/voice/tts", methods=["POST"])
def sarvam_tts_route():
    try:
        data = request.json or {}
        text = data.get("text")
        if not text:
            return jsonify({"error": "Missing text field"}), 400
            
        language = data.get("language", "en-IN")
        speaker = data.get("speaker", "meera")
        
        res = synthesize_speech_sarvam(text, target_language_code=language, speaker=speaker)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e), "engine": "error"}), 500


# --- FULL VOICE PIPELINE (DEEPGRAM STT -> GROQ LLM -> SARVAM AI TTS) ---
@voice_assistant_bp.route("/api/voice/process-full", methods=["POST"])
def process_full_voice():
    try:
        data = request.json or {}
        text_query = data.get("query")
        
        if not text_query:
            audio_file = request.files.get("audio")
            if audio_file:
                stt_res = transcribe_audio_bytes(audio_file.read())
                text_query = stt_res.get("transcript")
                
        if not text_query:
            return jsonify({"error": "Unable to transcribe or missing query"}), 400

        system_prompt = (
            "You are Salesbot AI Voice Assistant. Provide ultra-concise, natural responses (1-2 sentences) "
            "suitable for text-to-speech reading. Do not use markdown."
        )
        ai_response = generate_ai_response(text_query, system_prompt=system_prompt, json_mode=False)
        tts_res = synthesize_speech_sarvam(ai_response, target_language_code="en-IN")
        
        return jsonify({
            "transcript": text_query,
            "response": ai_response,
            "stt_engine": "deepgram",
            "tts_engine": tts_res.get("engine"),
            "audio_base64": tts_res.get("audio_base64")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
