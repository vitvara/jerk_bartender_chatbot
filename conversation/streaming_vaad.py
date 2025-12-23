import sounddevice as sd
import numpy as np
import time
import torch
import numpy as np

class SileroVAD:
    def __init__(self):
        self.model, self.utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True
        )

        (self.get_speech_timestamps,
         self.save_audio,
         self.read_audio,
         self.VADIterator,
         self.collect_chunks) = self.utils

        self.model.eval()

    def is_speech(self, audio_float32, sample_rate=16000):
        """
        audio_float32: numpy array, float32, mono, -1..1
        """
        audio_tensor = torch.from_numpy(audio_float32)
        speech_prob = self.model(audio_tensor, sample_rate).item()
        return speech_prob > 0.5, speech_prob


class StreamingVAAD:
    def __init__(
        self,
        sample_rate=16000,
        block_size=512,
        speech_threshold=0.6,
        silence_timeout=0.8
    ):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.speech_threshold = speech_threshold
        self.silence_timeout = silence_timeout

        self.vad = SileroVAD()

    def listen(self):
        print("🎤 Listening (neural VAAD)...")

        buffer = []
        recording = False
        silence_start = None

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self.block_size,
        ) as stream:

            while True:
                audio, _ = stream.read(self.block_size)
                audio = audio.flatten()

                is_speech, prob = self.vad.is_speech(audio)

                if is_speech:
                    if not recording:
                        print("🔴 Speech start")
                        recording = True
                    buffer.append(audio)
                    silence_start = None

                elif recording:
                    if silence_start is None:
                        silence_start = time.time()

                    elif time.time() - silence_start > self.silence_timeout:
                        print("🟢 Speech end")
                        break

                    buffer.append(audio)

        return np.concatenate(buffer)
