import sys
from PyQt6.QtWidgets import QApplication

from conversation.client_openai import client
from conversation.streaming_vaad import StreamingVAAD
from conversation.conversation_base import conversation
from conversation.bartender import Bartender
from conversation.speak import speak
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    bartender = Bartender(
        client=client,
        v2t=StreamingVAAD(),
        conversation_base=conversation,
    )

    window = MainWindow(bartender, speak)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
