import cv2
from PyQt6.QtCore import QThread, pyqtSignal

class CameraThread(QThread):
    frame_ready = pyqtSignal(object)

    def run(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            self.frame_ready.emit(frame)
            self.msleep(30)  # ~30 FPS

        cap.release()