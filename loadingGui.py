import os
import PyQt5
from PyQt5.QtWidgets import QApplication, QFrame, QMainWindow, QLabel, QScrollArea, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QPalette, QBrush, QColor
import sys

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

imagePath = resource_path("images/loadingWindow")

class loadingWindow(QMainWindow):

    close_app_signal = pyqtSignal()
    loading_status_text = "Подключение к серверу... \nПопытка 1"
    
    def __init__(self):
        super().__init__()
        self._suppress_close_signal = False
        self.initUI()

    def display_update(self, new_status):
        self.loading_status_text = new_status
        self.initUI() 
        self.show()

    def closeEvent(self, event):
        if not self._suppress_close_signal:
            self.close_app_signal.emit()  
        else:
            self._suppress_close_signal = False
        event.accept()   

    def closeWithoutExit(self):
        self._suppress_close_signal = True
        self.close()

    def initUI(self):

        self.setWindowTitle(" ")
        self.setFixedSize(289, 191)
        self.setWindowIcon(QIcon(imagePath + "/icon.png"))
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)


        self.central = QWidget()
        self.setCentralWidget(self.central)

        #загрузка картинок
        bg_pix = QPixmap(imagePath + "/background.png")

        close_btn_pix = imagePath + "/crossIcon.png"

        window_highlight_pix = QPixmap(imagePath + "/WindowHighthlight")

        font = QFont("Ubuntu", 10)
        font.setWeight(60) 

        #фон окна
        self.bg_label = QLabel(self.central)
        self.bg_label.setPixmap(bg_pix)
        self.bg_label.setGeometry(0, 0, 289, 191)

        #надпись о загрузке

        text_label = QLabel("Загрузка", self.central)
        text_label.setFont(QFont("Ubuntu", pointSize=10, weight=300))
        text_label.setGeometry(110, 29, 150, 50)
        text_label.setStyleSheet("color: ##718B46;")

        #надпись о статусе загрузке

        text_status = QLabel(self.loading_status_text, self.central)
        text_status.setFont(QFont("Ubuntu", pointSize=10, weight=300))
        text_status.setGeometry(40, 90, 170, 50)
        text_label.setStyleSheet("color: #718B46;")

        #кнопка закрытия окна

        self.close_btn = QPushButton(self.central)
        self.close_btn.setGeometry(225, 33, 22, 22)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                image: url({close_btn_pix.replace('\\', '/')});
            }}            
        """) 
        self.close_btn.clicked.connect(self.close)

        #блик

        window_highlight_label = QLabel(self.central)
        window_highlight_label.setPixmap(window_highlight_pix)
        window_highlight_label.setGeometry(15, 30, window_highlight_pix.width(), window_highlight_pix.height())
        window_highlight_label.setAttribute(Qt.WA_TransparentForMouseEvents)

