from openai import OpenAI
import sounddevice as sd
import wave
import numpy as np
import io
from conversation.client_openai import client

def speak(text, voice="ballad"):
    # Request WAV audio from OpenAI
    print('speak')
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text,
        response_format="wav"   # IMPORTANT
    )
    print('end')
    # Load WAV bytes into memory
    wav_bytes = response.read()
    wav_buffer = io.BytesIO(wav_bytes)

    # Read WAV from memory and play
    with wave.open(wav_buffer, "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16)

        sd.play(audio, wf.getframerate())
        sd.wait()
