from PyQt6.QtCore import QThread, pyqtSignal

class TTSWorker(QThread):
    started = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, speak_fn, text):
        super().__init__()
        self.speak_fn = speak_fn
        self.text = text

    def run(self):
        self.speak_fn(self.text)
        self.finished.emit()
