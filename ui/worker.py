from PyQt6.QtCore import QThread, pyqtSignal


class BartenderWorker(QThread):
    state_changed = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, bartender, image_bytes=None):
        super().__init__()
        self.bartender = bartender
        self.image_bytes = image_bytes

    def run(self):
        try:
            result = self.bartender.run_once(
                on_stage=self.state_changed.emit,
                image_bytes=self.image_bytes
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
