import os
import requests
import speech_recognition as sr
import sounddevice as sd
import numpy as np
import base64
import re
import time
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()  # Load environment variables from a .env file
# It's highly recommended to set your API key as an environment variable
# for security. Create a file named .env and add: GEMINI_API_KEY="YOUR_API_KEY"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

TEXT_GEN_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={GEMINI_API_KEY}"
TTS_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={GEMINI_API_KEY}"


def get_structured_response_from_audio(audio_b64):
    """
    Sends audio to Gemini, gets a structured response with transcription
    and a generated answer, then parses it. This reduces latency by
    combining STT and text generation into a single API call.
    """
    print("🧠 Transcribing and Thinking...")

    prompt = (
        "You are a voice assistant. Please transcribe the user's audio query and then provide a "
        "concise, helpful response. Format your entire output *exactly* as follows, with nothing "
        "before or after:\n\n"
        "Transcription: [The transcribed text]\n"
        "Response: [Your response to the query]"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": "audio/wav", "data": audio_b64}}
                ]
            }
        ]
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(TEXT_GEN_URL, json=payload, headers=headers)
        response.raise_for_status()

        result = response.json()
        full_text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")

        if not full_text:
            print("❌ Model returned an empty response.")
            return None, None

        # --- Parse the structured response ---
        transcription = None
        assistant_response = None

        lines = full_text.strip().split('\n')
        for line in lines:
            if line.lower().startswith("transcription:"):
                transcription = line[len("transcription:"):].strip()
            elif line.lower().startswith("response:"):
                assistant_response = line[len("response:"):].strip()

        if transcription and assistant_response:
            return transcription, assistant_response
        else:
            print(f"⚠️ Could not parse the model's response: {full_text}")
            # Fallback: Treat the whole thing as the response, but assume transcription failed.
            return "Transcription failed.", full_text

    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Error: {e}")
        # Try to parse the error message from the API if possible
        try:
            error_details = response.json()
            error_message = error_details.get("error", {}).get("message", "No details available.")
            # Return error message in a way that the main loop can handle
            return "API Error", f"An API error occurred: {error_message}"
        except (ValueError, AttributeError):
            return "API Error", "An API error occurred. Please check your connection and API key."
    except (IndexError, KeyError) as e:
        print(f"❌ Could not parse API response structure: {e}")
        return None, None


def speak_text(text_to_speak):
    """
    Sends text to the Gemini TTS API, gets the audio data, and plays it.
    """
    print("🗣️ Speaking...")
    payload = {
        "contents": [{"parts": [{"text": text_to_speak}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}}
            }
        },
        "model": "gemini-2.5-flash-preview-tts"
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(TTS_URL, json=payload, headers=headers)
        response.raise_for_status()

        result = response.json()
        part = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0]
        audio_data_b64 = part.get("inlineData", {}).get("data")
        mime_type = part.get("inlineData", {}).get("mimeType")

        if not audio_data_b64 or not mime_type or not mime_type.startswith("audio/L16"):
            print("❌ Invalid audio data received.")
            return

        # Extract sample rate from mimeType (e.g., "audio/L16;rate=24000")
        sample_rate_match = re.search(r"rate=(\d+)", mime_type)
        if not sample_rate_match:
            print("❌ Could not determine sample rate.")
            return
        sample_rate = int(sample_rate_match.group(1))

        # Decode base64 and convert to NumPy array for playback
        audio_data = base64.b64decode(audio_data_b64)
        pcm_data = np.frombuffer(audio_data, dtype=np.int16)

        # Play the audio
        sd.play(pcm_data, samplerate=sample_rate)
        sd.wait()  # Wait for the audio to finish playing

    except requests.exceptions.RequestException as e:
        print(f"❌ TTS API Request Error: {e}")
    except Exception as e:
        print(f"❌ An error occurred during audio playback: {e}")


def listen_for_command():
    """
    Uses the microphone to listen and returns the recorded audio as
    base64 encoded WAV data.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎤 Listening... (speak now)")
        recognizer.pause_threshold = 1.0  # seconds of non-speaking audio before phrase is considered complete
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)

            # Get WAV data from the recorded audio and encode it to base64
            wav_data = audio.get_wav_data()
            return base64.b64encode(wav_data).decode('utf-8')

        except sr.WaitTimeoutError:
            print("👂 Listening timed out, please try again.")
            return None
        except Exception as e:
            print(f"An error occurred while listening: {e}")
            return None


def main():
    """
    Main loop for the voice assistant.
    """
    if not GEMINI_API_KEY:
        print("=" * 50)
        print("🔴 FATAL ERROR: GEMINI_API_KEY is not set!")
        print("Please create a '.env' file in the same directory")
        print("and add the line: GEMINI_API_KEY=\"YOUR_API_KEY\"")
        print("You can get an API key from Google AI Studio.")
        print("=" * 50)
        return

    print("=" * 50)
    print("🚀 Gemini Voice Assistant Initialized 🚀")
    print("Say 'goodbye' to exit the program.")
    print("=" * 50)

    # Initial greeting
    greeting = "Hello! How can I help you today?"
    print(f"🤖 Assistant: {greeting}")
    speak_text(greeting)

    while True:
        audio_b64 = listen_for_command()

        if audio_b64:
            transcription, response_text = get_structured_response_from_audio(audio_b64)

            if transcription and response_text:
                print(f"👤 You said: {transcription}")

                if "goodbye" in transcription.lower():
                    farewell = "Goodbye! Have a great day."
                    print(f"🤖 Assistant: {farewell}")
                    speak_text(farewell)
                    break

                print(f"🤖 Assistant: {response_text}")
                speak_text(response_text)
            else:
                # Handle cases where the API call or parsing failed
                speak_text("Sorry, I had trouble processing that. Please try again.")
        else:
            # If listening failed, wait a moment before listening again
            time.sleep(1)


if __name__ == "__main__":
    main()

