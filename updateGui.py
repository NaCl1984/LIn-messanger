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

imagePath = resource_path("images/updateWindow")

class updateWindow(QMainWindow):
    
    updateLater_signal = pyqtSignal()
    update_signal = pyqtSignal(str)
    isCriticalUpdate = False
    updateUrl = ""

    def __init__(self):
        super().__init__()
        self.initUI()

    def updateNow(self):
        self.update_signal.emit(self.updateUrl)

    def updateLater(self):
        self.updateLater_signal.emit()

    def display_update(self, url, critical):
        self.updateUrl = url
        self.isCriticalUpdate = critical
        # Здесь можно обновить текст чейнджлога, если добавишь QLabel для него
        self.initUI() # Пересобираем кнопки
        self.show()

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
        
        empty_btn_pix = {
            "idle":imagePath + "/emptyBtnIdle",
            "hover":imagePath + "/emptyBtnHover",
            "pressed":imagePath + "/emptyBtnPressed"
        }

        close_btn_pix = imagePath + "/crossIcon.png"

        window_highlight_pix = QPixmap(imagePath + "/WindowHighthlight")



        font = QFont("Ubuntu", 10)
        font.setWeight(60) 

        #фон окна
        self.bg_label = QLabel(self.central)
        self.bg_label.setPixmap(bg_pix)
        self.bg_label.setGeometry(0, 0, 289, 191)

        #надпись о том что устройство не распознанно

        text_label = QLabel("Available new version", self.central)
        text_label.setFont(QFont("Ubuntu", pointSize=10, weight=300))
        text_label.setGeometry(78, 29, 150, 50)
        text_label.setStyleSheet("color: #3C4A25;")

        #кнопка update

        

        self.update_btn = QPushButton(self.central)
        self.update_btn.setGeometry(289//2 - 90//2, 80, 90, 32)
        self.update_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                image: url({empty_btn_pix['idle'].replace('\\', '/')});
            }}
            QPushButton:hover {{
                image: url({empty_btn_pix['hover'].replace('\\', '/')});
            }}
            QPushButton:pressed {{
                image: url({empty_btn_pix['pressed'].replace('\\', '/')});
            }}
        """) 
        self.update_btn.clicked.connect(self.updateNow)

        update_btn_label = QLabel("Update",self.central)
        update_btn_label.setGeometry(289//2 - 90//2 + 21, 78, 90, 32)
        update_btn_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        update_btn_label.setFont(QFont("Ubuntu", pointSize=10, weight=300))
        update_btn_label.setStyleSheet("color: #3C4A25;")

        #кнопка later

        
        if not self.isCriticalUpdate:
            self.later_btn = QPushButton(self.central)
            self.later_btn.setGeometry(289//2 - 90//2, 110, 90, 32)
            self.later_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    image: url({empty_btn_pix['idle'].replace('\\', '/')});
                }}
                QPushButton:hover {{
                    image: url({empty_btn_pix['hover'].replace('\\', '/')});
                }}
                QPushButton:pressed {{
                    image: url({empty_btn_pix['pressed'].replace('\\', '/')});
                }}
            """) 
            self.later_btn.clicked.connect(self.updateLater)

            later_btn_label = QLabel("Later",self.central)
            later_btn_label.setGeometry(289//2 - 90//2 + 27, 108, 90, 32)
            later_btn_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            later_btn_label.setFont(QFont("Ubuntu", pointSize=10, weight=300))
            later_btn_label.setStyleSheet("color: #3C4A25;")

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



        