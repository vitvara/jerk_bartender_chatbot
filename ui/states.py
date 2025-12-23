from enum import Enum

class AppState(str, Enum):
    READY = "Ready"
    LISTENING = "Listening"
    PROCESSING = "Processing"
    SPEAKING = "Speaking"
    ERROR = "Error"
