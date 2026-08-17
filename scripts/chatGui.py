import json
import os
import PyQt5
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QTextEdit, QLineEdit, QPushButton, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont, QIcon, QTextCursor
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QPalette, QBrush, QColor
import sys


def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

imagePath =  resource_path("images/chatWindow")

class scrollbar_point_widget(QLabel):
            
    valueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dragging = False
        self.drag_start_y = 0
        self.start_y = 0
        self.min_y = 86
        self.max_y = 434
        self.setPixmap(QPixmap(imagePath + "/scrollbarVertical.png"))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_y = event.globalY()
            self.start_y = self.y()

    def mouseMoveEvent(self, event):
        if self.dragging:
            dy = event.globalY() - self.drag_start_y
            new_y = self.start_y + dy
            # Ограничиваем
            new_y = max(self.min_y, min(self.max_y, new_y))
            self.move(self.x(), new_y)
            # Вычисляем значение (0..100)
            fraction = (new_y - self.min_y) / (self.max_y - self.min_y)
            value = int(fraction * 100)
            self.valueChanged.emit(value)
        
    def mouseReleaseEvent(self, event):
        self.dragging = False
    
    def setValue(self, value):
        # value от 0 до 100
        y = self.min_y + (value / 100) * (self.max_y - self.min_y)
        self.move(self.x(), int(y))
        self.valueChanged.emit(value)

    def wheelEvent(self, event):
        delta = event.angleDelta().y() // 120
        # Получаем текущее значение (0..100) из положения
        fraction = (self.y() - self.min_y) / (self.max_y - self.min_y) if self.max_y > self.min_y else 0
        value = int(fraction * 100)
        new_val = value - delta  # подбери знак, если надо
        new_val = max(0, min(100, new_val))
        # Устанавливаем новое значение (переместит ползунок и испустит сигнал)
        self.setValue(new_val)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            # Прокрутка колесиком – передаём событие ползунку (он сам изменит значение)
            self.wheelEvent(event)
            return True
        return super().eventFilter(obj, event)

class ChatWindow(QMainWindow):
    sendMessage_signal = pyqtSignal(str)
    USER_INFO_PATH = ''
    
    def __init__(self):
        super().__init__()
        self.initUI()

    def closeEvent(self, event):
        # При закрытии окна чата завершаем всё приложение
        QApplication.quit()
        super().closeEvent(event)

    def on_text_scrolled(self, value):
        vbar = self.chat_text.verticalScrollBar()
        max_val = vbar.maximum() - vbar.minimum()
        if max_val > 0:
            fraction = (value - vbar.minimum()) / max_val
            self.scrollbar_point.blockSignals(True)          # отключаем сигналы, чтобы не зациклиться
            self.scrollbar_point.setValue(int(fraction * 100))
            self.scrollbar_point.blockSignals(False)

    def on_handle_moved(self, value):
            # Прокручиваем текст пропорционально положению ползунка.
            vbar = self.chat_text.verticalScrollBar()
            vbar.setValue(int(value / 100 * (vbar.maximum() - vbar.minimum())) + vbar.minimum())

    def sendMessage(self):
        msg = self.text_entry.text().strip()
        self.text_entry.clear()
        self.sendMessage_signal.emit(msg)
        with open(self.USER_INFO_PATH, "r", encoding="utf-8") as f:
            userNickname = json.load(f)["nickname"]
        
        # content = self.chat_text.toPlainText().strip()
        
        # if content:
        #     # Если в чате уже что-то есть, добавляем два переноса
        #     new_text = content + "\n\n" + f"{userNickname}: {msg}"
        # else:
        #     # Если чат пустой (первое сообщение), просто пишем текст
        #     new_text = f"{userNickname}: {msg}"
            
        # # Устанавливаем текст заново
        # self.chat_text.setPlainText(new_text)
        self.chat_text.insertPlainText(f"{userNickname}: {msg}\n\n")
        # Скроллим вниз
        self.chat_text.moveCursor(QTextCursor.End)
        self.vbar.setValue(self.vbar.maximum())

    def setContactNickname(self, nickname):
        self.nickname_text.setText(nickname)
        self.send_btn.setEnabled(True)

    def setChatHistory(self, messages):
        self.chat_text.clear()
        textToAdd = ''
        for msg in messages:
            textToAdd += msg.get("from") + ": " + msg.get("text") + "\n\n"
        self.chat_text.setText(textToAdd)
        cursor = self.chat_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_text.setTextCursor(cursor)
        self.chat_text.ensureCursorVisible()

    def setStatusConnected(self):
        self.status_icon_label.setPixmap(self.status_connecting_pix["statusConnected"])

    def setStatusNotConnected(self):
        self.status_icon_label.setPixmap(self.status_connecting_pix["statusNotConnected"])

    def addMessage(self, msg):
        self.chat_text.insertPlainText(msg.get("from") + ": " + str(msg.get("text")) + "\n\n")
        self.chat_text.moveCursor(QTextCursor.End)
        self.vbar.setValue(self.vbar.maximum())

    def initUI(self):

        self.setWindowTitle(" ")
        self.setFixedSize(500, 600)
        self.setWindowIcon(QIcon(imagePath + "/icon.png"))

        self.central = QWidget()
        self.setCentralWidget(self.central)

        scrollbar_point_pix = QPixmap(imagePath + "/scrollbarVertical.png")
        bg_pix = QPixmap(imagePath + "/background.png")
        chat_field_pix = QPixmap(imagePath + "/chatField.png")
        scrollbar_line_pix = QPixmap(imagePath + "/scrollbarLine.png")
        light_pix = QPixmap(imagePath + "/light.png")
        msg_entry_field_pix = QPixmap(imagePath + "/messageEntryField.png")
        send_btn_pix = { "idle" : QPixmap(imagePath + "/sendMessagesBtn_idle.png"),
                        "pressed" : QPixmap(imagePath + "/sendMessagesBtn_pressed.png"),
                        "hover" : QPixmap(imagePath + "/sendMessagesBtn_hover.png")
                        }
        nickname_field_pix = QPixmap(imagePath + "/nicknameEntryField.png")
        status_place_pix = QPixmap(imagePath + "/statusIconPlace.png")
        self.status_connecting_pix ={ "statusConnecting" : QPixmap(imagePath + "/statusConneting.png"),
                                "statusConnected" : QPixmap(imagePath + "/statusConnected.png"),
                                "statusNotConnected" : QPixmap(imagePath + "/statusNotConnected.png")
                                }

        sendBtnPath = {
            "idle": imagePath + "/sendMessagesBtn_idle.png",
            "hower": imagePath + "/sendMessagesBtn_hover.png",
            "pressed": imagePath + "/sendMessagesBtn_pressed.png",
            "disable": imagePath + "/sendMessagesBtn_pressed.png"
        }

        font = QFont("Ubuntu", 10)
        font.setWeight(60) 

        self.bg_label = QLabel(self.central)
        self.bg_label.setPixmap(bg_pix)
        self.bg_label.setGeometry(0, 0, 500, 600)

        #фон поля чата
        chat_field_label = QLabel(self.central)
        chat_field_label.setPixmap(chat_field_pix)
        chat_field_label.setGeometry(26, int(278 - chat_field_pix.height()/2), chat_field_pix.width(), chat_field_pix.height())

        # Текстовое поле чата (аналог ScrolledText)
        self.chat_text = QTextEdit(self.central)
        self.chat_text.setGeometry(64, 87, 360, 370)
        #chat_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.chat_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_text.setStyleSheet("QTextEdit {background: transparent;border: none;color: #3C4A25}QScrollBar:vertical {background: transparent;width: 18px;}QScrollBar::handle:vertical {background: url(images/scrollbarVertical.png); background-repeat: no-repeat; min-height: 30px;max-height: 30px;}QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {height: 0px;background: none;}QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {background: transparent;}")
        self.chat_text.setFont(font)
        self.chat_text.setReadOnly(True)
        self.chat_text.document().setDocumentMargin(0)
        self.chat_text.setHtml("")

        # Декоративная линия скроллбара
        scrollbar_line_label = QLabel(self.central)
        scrollbar_line_label.setPixmap(scrollbar_line_pix)
        scrollbar_line_label.setGeometry(403, 62, scrollbar_line_pix.width(), scrollbar_line_pix.height())

        self.scrollbar_point = scrollbar_point_widget(self.central)
        self.scrollbar_point.move(427, 86)

        self.vbar = self.chat_text.verticalScrollBar()
        self.vbar.valueChanged.connect(self.on_text_scrolled)

        self.scrollbar_point.valueChanged.connect(self.on_handle_moved)

        self.chat_text.installEventFilter(self.scrollbar_point)

        # Блик
        light_label = QLabel(self.central)
        light_label.setPixmap(light_pix)
        light_label.setGeometry(47, 79, light_pix.width(), light_pix.height())
        light_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Фон поля ввода сообщения
        msg_entry_bg = QLabel(self.central)
        msg_entry_bg.setPixmap(msg_entry_field_pix)
        msg_entry_bg.setGeometry(42, int(523 - msg_entry_field_pix.height()/2) , msg_entry_field_pix.width(), msg_entry_field_pix.height())

        # Поле ввода сообщения
        self.text_entry = QLineEdit(self.central)
        self.text_entry.setGeometry(60, 511, 325, 17)
        self.text_entry.setStyleSheet("background: transparent; border: none; color: #3C4A25") 
        self.text_entry.setFont(QFont("Ubuntu", pointSize=10, weight=4000))
        self.text_entry.returnPressed.connect(self.sendMessage)
        self.text_entry.setPlaceholderText("Type your message here")

        # Кнопка отправки 
        self.send_btn = QPushButton(self.central)
        self.send_btn.setGeometry(396, int(521 - send_btn_pix["idle"].height()/2), send_btn_pix["idle"].width(), send_btn_pix["idle"].height())
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                image: url({sendBtnPath['idle'].replace('\\', '/')});
            }}
            QPushButton:hover {{
                image: url({sendBtnPath['hower'].replace('\\', '/')});
            }}
            QPushButton:pressed {{
                image: url({sendBtnPath['pressed'].replace('\\', '/')});
            }}
            QPushButton:disabled {{
                image: url({sendBtnPath['disable'].replace('\\', '/')});
            }}
        """) 
        self.send_btn.clicked.connect(self.sendMessage)
        self.send_btn.setEnabled(False) 

        # Фон поля ника собеседника
        nickname_bg = QLabel(self.central)
        nickname_bg.setPixmap(nickname_field_pix)
        nickname_bg.setGeometry(42, int(46 - nickname_field_pix.height()/2), nickname_field_pix.width(), nickname_field_pix.height())

        # Надпись "Chat with:"
        you_are_label = QLabel("Chat with: ", self.central)
        you_are_label.setGeometry(50, 10, 60, 15)
        you_are_label.setFont(font)
        you_are_label.setStyleSheet("color: #3C4A25;")

        # Поле ника собеседника
        self.nickname_text = QLabel(self.central)
        self.nickname_text.setGeometry(58, 32, 125, 20)
        self.nickname_text.setStyleSheet("background: transparent; border: none;") 
        self.nickname_text.setFont(font)
        self.nickname_text.setStyleSheet("color: #3C4A25;")

        # Место под статус-иконку 
        status_place_label = QLabel(self.central)
        status_place_label.setPixmap(status_place_pix)
        status_place_label.setGeometry(409, int(41 - status_place_pix.height()/2), status_place_pix.width(), status_place_pix.height())

        # Сама статус-иконка
        self.status_icon_label = QLabel(self.central)
        self.status_icon_label.setPixmap(self.status_connecting_pix["statusConnecting"])
        self.status_icon_label.setGeometry(416, int(45 - self.status_connecting_pix["statusConnecting"].height()/2), self.status_connecting_pix["statusConnecting"].width(), self.status_connecting_pix["statusConnecting"].height())
