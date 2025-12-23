import io
import json
import base64
from scipy.io import wavfile
from openai import OpenAI


class Bartender:
    def __init__(self, client: OpenAI, v2t, conversation_base):
        self.client = client
        self.v2t = v2t
        self.conversation = conversation_base.copy()
        self.orders = []

    # ---------- utils ----------
    def image_bytes_to_data_url(self, image_bytes: bytes) -> str:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    # ---------- main ----------
    def run_once(self, on_stage=None, image_bytes=None):
        def stage(s):
            if on_stage:
                on_stage(s)

        # 🎤 Listening
        stage("listening")
        audio = self.v2t.listen()

        # ⚙️ Speech → Text
        stage("processing")
        buf = io.BytesIO()
        wavfile.write(buf, 16000, audio)
        buf.seek(0)

        transcript = self.client.audio.transcriptions.create(
            file=("speech.wav", buf, "audio/wav"),
            model="gpt-4o-transcribe",
            language='th'
        )

        user_text = transcript.text
        print("USER:", user_text)

        # ---------- Build USER message ----------
        if image_bytes is not None:
            image_url = self.image_bytes_to_data_url(image_bytes)

            user_message = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        else:
            user_message = {
                "role": "user",
                "content": user_text
            }

        self.conversation.append(user_message)

        # ---------- LLM ----------
        response = self.client.chat.completions.create(
            model="gpt-5.2-chat-latest",
            messages=self.conversation
        )
        print('Finish')
        raw = response.choices[0].message.content
        data = json.loads(raw)

        self.conversation.append({
            "role": "assistant",
            "content": raw
        })

        confirmed = data.get("order_status") == "confirmed"
        detail = data.get("order_detail")
       
        if confirmed:
            self.orders.append(detail)
        print('check Order')
        return {
            "user": user_text,
            "assistant": data["conversation"],
            "order_confirmed": confirmed,
            "order_detail": detail
        }
