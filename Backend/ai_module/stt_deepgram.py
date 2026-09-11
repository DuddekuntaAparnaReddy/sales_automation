import os
import requests

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")

def transcribe_audio_bytes(audio_bytes, mimetype="audio/wav", language="en"):
    """
    Transcribes audio bytes using Deepgram Speech-to-Text (STT) REST API.
    Uses 'nova-2' model with smart formatting for high transcription accuracy.
    Falls back gracefully if API key is unconfigured or request fails.
    """
    if not DEEPGRAM_API_KEY:
        print("[DEEPGRAM STT] DEEPGRAM_API_KEY not configured in environment. Using fallback mode.")
        return {"transcript": "", "confidence": 0.0, "engine": "fallback", "message": "Deepgram API key not provided."}

    try:
        url = f"https://api.deepgram.com/v1/listen?model=nova-2&smart_formatting=true&language={language}"
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": mimetype
        }
        
        response = requests.post(url, headers=headers, data=audio_bytes, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            channels = res_data.get("results", {}).get("channels", [])
            if channels and len(channels) > 0:
                alternatives = channels[0].get("alternatives", [])
                if alternatives and len(alternatives) > 0:
                    transcript = alternatives[0].get("transcript", "")
                    confidence = alternatives[0].get("confidence", 0.0)
                    return {
                        "transcript": transcript,
                        "confidence": confidence,
                        "engine": "deepgram",
                        "model": "nova-2"
                    }
        
        print(f"[DEEPGRAM STT ERROR] Status {response.status_code}: {response.text}")
        return {"transcript": "", "confidence": 0.0, "engine": "deepgram_error", "error": response.text}

    except Exception as e:
        print(f"[DEEPGRAM STT EXCEPTION] {e}")
        return {"transcript": "", "confidence": 0.0, "engine": "error", "error": str(e)}
