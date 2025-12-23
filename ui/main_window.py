from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QPropertyAnimation, QTimer

from ui.worker import BartenderWorker
from ui.tts_worker import TTSWorker
import cv2
from PyQt6.QtGui import QImage, QPixmap
from vision.camera_thread import CameraThread
from vision.camera_utils import frame_to_jpeg_bytes


# -------------------- Chat Bubble --------------------

class ChatBubble(QFrame):
    def __init__(self, text, is_user=False):
        super().__init__()
        self.setObjectName("UserBubble" if is_user else "BotBubble")

        layout = QVBoxLayout(self)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(label)

        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(220)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.start()


# -------------------- Order Card --------------------

class OrderCard(QFrame):
    def __init__(self, order_data, on_finish):
        super().__init__()
        self.setObjectName("OrderCard")
        self.on_finish = on_finish

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        title = QLabel(f"🍹 {order_data['drink_name']}")
        title.setObjectName("OrderTitle")
        layout.addWidget(title)

        layout.addWidget(QLabel("🧾 Ingredients"))
        for i in order_data.get("ingredients", []):
            layout.addWidget(QLabel(f"• {i.strip()}"))

        layout.addWidget(QLabel("🧑‍🍳 How to make"))
        for step in order_data.get("how_to_make", []):
            layout.addWidget(QLabel(f"• {step.strip()}"))

        finish_btn = QPushButton("✅ Finish")
        finish_btn.setObjectName("FinishButton")
        finish_btn.clicked.connect(self.finish)

        layout.addWidget(finish_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def finish(self):
        self.on_finish(self)

from PyQt6.QtGui import QTextOption
class ChatBubble(QFrame):
    def __init__(self, text, is_user=False):
        super().__init__()
        self.setObjectName("UserBubble" if is_user else "BotBubble")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)

        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        self.text_view.setText(text)
        self.text_view.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.text_view.setFrameStyle(QFrame.Shape.NoFrame)

        self.text_view.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.text_view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.text_view.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )

        # 🔥 Recalculate height when text layout changes
        self.text_view.document().documentLayout().documentSizeChanged.connect(
            self._update_size
        )

        layout.addWidget(self.text_view)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_size()

    def _update_size(self):
        doc = self.text_view.document()

        # IMPORTANT: set text width to viewport width
        doc.setTextWidth(self.text_view.viewport().width())

        height = int(doc.size().height()) + 10
        self.text_view.setFixedHeight(height)


    


# -------------------- Main Window --------------------

class MainWindow(QWidget):
    def __init__(self, bartender, speak_fn):
        super().__init__()
        self.bartender = bartender
        self.speak_fn = speak_fn

        self.setWindowTitle("🍺 Jerk Bartender")
        self.resize(1100, 720)
        self.setStyleSheet(self.style())

        root = QVBoxLayout(self)
        root.setSpacing(12)

        # ================= HEADER =================
        header = QHBoxLayout()
        title = QLabel("🍺 Jerk Bartender")
        title.setObjectName("Header")

        self.status = QLabel("● Ready")
        self.status.setObjectName("Status")

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.status)
        root.addLayout(header)

        # ================= MAIN AREA =================
        main = QHBoxLayout()
        root.addLayout(main, 1)

        # -------- CAMERA (MAIN PANEL) --------
        self.camera_label = QLabel("📹 Camera")
        self.camera_label.setObjectName("CameraView")
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setMinimumHeight(380)

        main.addWidget(self.camera_label, 3)

        # -------- ORDERS (SIDE PANEL) --------
        self.orders_layout = QVBoxLayout()
        self.orders_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        orders_container = QWidget()
        orders_container.setLayout(self.orders_layout)

        orders_scroll = QScrollArea()
        orders_scroll.setWidgetResizable(True)
        orders_scroll.setWidget(orders_container)

        orders_card = self.card("🍻 Orders", orders_scroll)
        orders_card.setMaximumWidth(360)

        main.addWidget(orders_card, 1)

        # ================= CONVERSATION =================
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(8)
        



        chat_container = QWidget()
        chat_container.setLayout(self.chat_layout)
        chat_container.setMinimumWidth(800)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setWidget(chat_container)
        self.chat_scroll.setMinimumHeight(200)

        root.addWidget(self.card("💬 Conversation", self.chat_scroll))

        # ================= ACTION =================
        self.btn = QPushButton("🎤 Talk")
        self.btn.setObjectName("TalkButton")
        self.btn.clicked.connect(self.start)
        root.addWidget(self.btn)

        # ================= CAMERA THREAD =================
        self.latest_frame = None
        self.camera_thread = CameraThread()
        self.camera_thread.frame_ready.connect(self.update_camera)
        self.camera_thread.start()


    def update_camera(self, frame):
        self.latest_frame = frame

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)

        pix = QPixmap.fromImage(img).scaled(
            self.camera_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.camera_label.setPixmap(pix)

    # ---------------- Actions ----------------

    def start(self):
        self.btn.setEnabled(False)
        self.status.setText("🎤 Listening…")

        image_bytes = None
        if self.latest_frame is not None:
            image_bytes = frame_to_jpeg_bytes(self.latest_frame)
            print('capture')

        self.worker = BartenderWorker(
            self.bartender,
            image_bytes=image_bytes
        )
        print('end')
        self.worker.state_changed.connect(self.on_state)
        self.worker.finished.connect(self.on_result)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_state(self, s):
        icons = {
            "listening": "🎤 Listening…",
            "processing": "⚙️ Processing…",
            "speaking": "🔊 Speaking…",
            "ready": "🟢 Ready"
        }
        self.status.setText(icons.get(s, s))

    def on_result(self, result):
        # User message
        user_bubble = ChatBubble(result["user"], True)
        self.chat_layout.addWidget(user_bubble, alignment=Qt.AlignmentFlag.AlignRight)

        # Assistant message
        bot_bubble = ChatBubble(result["assistant"], False)
        self.chat_layout.addWidget(bot_bubble, alignment=Qt.AlignmentFlag.AlignLeft)

        QTimer.singleShot(
            50,
            lambda: self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()
            )
        )

        # Speak async
        self.on_state("speaking")
        self.tts = TTSWorker(self.speak_fn, result["assistant"])
        self.tts.started.connect(lambda: self.status.setText("🔊 Speaking…"))
        self.tts.finished.connect(self.on_tts_done)
        self.tts.start()

        # Order card
        if result["order_confirmed"]:
            card = OrderCard(
                result["order_detail"],
                on_finish=self.remove_order
            )
            self.orders_layout.addWidget(card)

    def on_tts_done(self):
        self.status.setText("🟢 Ready")
        self.btn.setEnabled(True)

    def on_error(self, e):
        self.status.setText("❌ Error")
        self.btn.setEnabled(True)

    def remove_order(self, card):
        card.setParent(None)
        card.deleteLater()

    # ---------------- UI helpers ----------------

    def card(self, title, widget):
        frame = QFrame()
        frame.setObjectName("Card")
        layout = QVBoxLayout(frame)

        label = QLabel(title)
        label.setObjectName("CardTitle")

        layout.addWidget(label)
        layout.addWidget(widget)
        return frame

    def style(self):
        return """
    QWidget {
        background-color: #0f1115;
        color: #eaeaea;
        font-family: Segoe UI;
        font-size: 14px;
    }

    QLabel#Header {
        font-size: 26px;
        font-weight: bold;
    }

    QLabel#Status {
        font-size: 14px;
        color: #4caf50;
    }

    QFrame#Card {
        background-color: #181b22;
        border-radius: 18px;
        padding: 12px;
    }

    QLabel#CardTitle {
        font-size: 16px;
        font-weight: bold;
        padding-bottom: 8px;
    }

    QLabel#CameraView {
        background-color: #000;
        border-radius: 22px;
        font-size: 18px;
        color: #888;
    }

    QFrame#UserBubble {
        background-color: #2a2d35;
        border-radius: 16px;
        padding: 10px;
        margin: 6px;
        align-self: flex-end;
    }

    QFrame#BotBubble {
        background-color: #1f3b2c;
        border-radius: 16px;
        padding: 10px;
        margin: 6px;
    }

    QFrame#OrderCard {
        background-color: #20232b;
        border-radius: 16px;
        padding: 12px;
        margin-bottom: 12px;
    }

    QLabel#OrderTitle {
        font-size: 16px;
        font-weight: bold;
        color: #ffcc80;
    }

    QPushButton#FinishButton {
        background-color: #4caf50;
        color: black;
        border-radius: 14px;
        padding: 6px 14px;
        font-weight: bold;
    }

    QPushButton#TalkButton {
        background-color: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 #ff9800, stop:1 #ffb74d
        );
        color: black;
        border-radius: 26px;
        padding: 14px;
        font-size: 18px;
        font-weight: bold;
    }

    QPushButton#TalkButton:disabled {
        background-color: #444;
        color: #aaa;
    }

    QTextEdit {
        background: transparent;
        color: #eaeaea;
        font-size: 14px;
    }
    """

