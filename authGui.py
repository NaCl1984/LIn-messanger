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

imagePath = resource_path("images/authWindow")

class authWindow(QMainWindow):
    
    createNewAccount_signal = pyqtSignal()
    linkDevice_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.initUI()

    def linkRequest(self):
        self.linkDevice_signal.emit()

    def createNewAccountRequest(self):
        self.createNewAccount_signal.emit()

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
        
        link_btn_pix = {
            "idle":imagePath + "/linkBtnIdle",
            "hover":imagePath + "/linkBtnHover",
            "pressed":imagePath + "/linkBtnPressed"
        }

        createNewAccount_btn_pix = {
            "idle":imagePath + "/createNewAccountBtnIdle",
            "hover":imagePath + "/createNewAccountBtnHover",
            "pressed":imagePath + "/createNewAccountBtnPressed"
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

        text_label = QLabel("This device is not linked \nto this account", self.central)
        text_label.setFont(QFont("Ubuntu", pointSize=10, weight=300))
        text_label.setGeometry(40, 29, 150, 50)
        text_label.setStyleSheet("color: #3C4A25;")

        #кнопка подтверждения входа

        self.link_btn = QPushButton(self.central)
        self.link_btn.setGeometry(289//2 - 90//2, 80, 90, 32)
        self.link_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                image: url({link_btn_pix['idle'].replace('\\', '/')});
            }}
            QPushButton:hover {{
                image: url({link_btn_pix['hover'].replace('\\', '/')});
            }}
            QPushButton:pressed {{
                image: url({link_btn_pix['pressed'].replace('\\', '/')});
            }}
        """) 
        self.link_btn.clicked.connect(self.linkRequest)

        #кнопка создания нового пользователя

        self.createAccount_btn = QPushButton(self.central)
        self.createAccount_btn.setGeometry(289//2 - 150//2, 110, 150, 32)
        self.createAccount_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                image: url({createNewAccount_btn_pix['idle'].replace('\\', '/')});
            }}
            QPushButton:hover {{
                image: url({createNewAccount_btn_pix['hover'].replace('\\', '/')});
            }}
            QPushButton:pressed {{
                image: url({createNewAccount_btn_pix['pressed'].replace('\\', '/')});
            }}
        """) 
        self.createAccount_btn.clicked.connect(self.createNewAccountRequest)

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



        