import os
import requests

SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")

def synthesize_speech_sarvam(text, target_language_code="en-IN", speaker="meera"):
    """
    Synthesizes natural text-to-speech audio using Sarvam AI TTS API ('bulbul:v1').
    Supports native Indian accent rendering (hi-IN, te-IN, ta-IN, en-IN, etc.).
    Returns base64 encoded audio string and metadata.
    """
    if not SARVAM_API_KEY:
        print("[SARVAM TTS] SARVAM_API_KEY not configured in environment. Using fallback mode.")
        return {
            "audio_base64": None,
            "engine": "fallback",
            "message": "Sarvam AI API key not provided."
        }

    try:
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {
            "api-subscription-key": SARVAM_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": [text],
            "target_language_code": target_language_code,
            "speaker": speaker,
            "pitch": 0,
            "pace": 1.05,
            "loudness": 1.5,
            "speech_sample_rate": 8000,
            "enable_preprocessing": True,
            "model": "bulbul:v1"
        }

        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            audios = res_data.get("audios", [])
            if audios and len(audios) > 0:
                return {
                    "audio_base64": audios[0],
                    "format": "wav",
                    "engine": "sarvam",
                    "speaker": speaker,
                    "language": target_language_code
                }
                
        print(f"[SARVAM TTS ERROR] Status {response.status_code}: {response.text}")
        return {"audio_base64": None, "engine": "sarvam_error", "error": response.text}

    except Exception as e:
        print(f"[SARVAM TTS EXCEPTION] {e}")
        return {"audio_base64": None, "engine": "error", "error": str(e)}
