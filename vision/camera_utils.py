import cv2

def frame_to_jpeg_bytes(frame):
    ok, buf = cv2.imencode(".jpg", frame)
    return buf.tobytes() if ok else None
