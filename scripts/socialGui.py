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

imagePath = resource_path("images/socialWindow")

class scrollbar_point_widget(QLabel):
            
    valueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dragging = False
        self.drag_start_y = 0
        self.start_y = 0
        self.min_y = 173
        self.max_y = 450
        self.setPixmap(QPixmap(imagePath + "/scroll.png"))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_y = event.globalY()
            self.start_y = self.y()
        
    def mouseReleaseEvent(self, event):
        self.dragging = False

    def mouseMoveEvent(self, event):
        if self.dragging:
            dy = event.globalY() - self.drag_start_y
            new_y = self.start_y + dy
            # Ограничиваем физический ход
            new_y = max(self.min_y, min(self.max_y, new_y))
            self.move(self.x(), new_y)
            
            # Вычисляем процент (0..100) относительно доступного пути
            range_y = self.max_y - self.min_y
            if range_y > 0:
                fraction = (new_y - self.min_y) / range_y
                value_pct = int(fraction * 100)
                self.valueChanged.emit(value_pct)

    def setValue(self, value_pct):
        # Принимаем проценты, ограничиваем их
        value_pct = max(0, min(100, value_pct))
        # Пересчитываем в физическую координату Y
        range_y = self.max_y - self.min_y
        new_y = int(self.min_y + (value_pct / 100) * range_y)
        
        self.move(self.x(), new_y)
        # Важно: испускаем именно проценты
        self.valueChanged.emit(value_pct)


    def wheelEvent(self, event):
        delta = event.angleDelta().y() // 120
        # Получаем текущее значение (0..100) из положения
        fraction = (self.y() - self.min_y) / (self.max_y - self.min_y) if self.max_y > self.min_y else 0
        current_percent = int(fraction * 100)
        new_val = current_percent - (delta ) # Умножение на 5 для скорости
        self.setValue(new_val)
        value = int(fraction * 100)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            # Прокрутка колесиком – передаём событие ползунку (он сам изменит значение)
            self.wheelEvent(event)
            return True
        return super().eventFilter(obj, event)

class ContactItem(QWidget):
    # Сигнал, который сработает при клике на контакт
    clicked = pyqtSignal(str) 

    def set_selected(self, selected: bool):
        if selected:
            self.bg.show()
        else:
            self.bg.hide()

    def __init__(self, nickname, status, friendCode, parent=None):
        super().__init__(parent, Qt.Widget)
        bg_pix = QPixmap(imagePath + "/contact_select_highlight.png")
        self.setFixedSize(bg_pix.width(), bg_pix.height())
        self.nickname = nickname
        self.friendCode = friendCode

        # 1. Фон (подложка)
        self.bg = QLabel(self)
        self.bg.setPixmap(bg_pix)
        self.bg.setGeometry(0, 0, bg_pix.width(), bg_pix.height())
        self.bg.hide()

        # 2. Иконка статуса
        self.status_icon = QLabel(self)
        # Логика выбора картинки (упрощенно)
        status_pix = QPixmap(status) 
        self.status_icon.setPixmap(status_pix)
        self.status_icon.setGeometry(10, 6, 22, 22)

        # 3. Никнейм
        self.name_label = QLabel(nickname, self)
        self.name_label.setGeometry(33, 6, 150, 20)
        self.name_label.setFont(QFont("Ubuntu", pointSize=10, weight=4000))
        self.name_label.setStyleSheet("color: #3C4A25;")


        # 4. Прозрачная кнопка ПОВЕРХ всего
        self.btn = QPushButton(self)
        self.btn.setGeometry(0, 0, 260, 50)
        self.btn.setStyleSheet("background: transparent; border: none;")
        self.btn.clicked.connect(lambda: self.clicked.emit(self.nickname))

class SocialWindow(QMainWindow):
    contacts = [] 
    selectedContact = None
    selectedStatus = "joy"

    selectedStatusMenu = {
        "joy": (28, 30),
        "happy": (28+34, 30),
        "neutral": (28+34+35, 30),
        "sad": (28+34+35+35, 30),
        "angry": (28+34+35+35+35, 30),
        "sick": (28, 75),
        "cool": (28+34, 75),
        "love": (28+34+35, 75),
        "sleepy": (28+34+35+35, 75),
        "busy": (28+34+35+35+35, 75),
    }
    
    statusCodesToNames = {
        -1:"offline",
        1:"joy",
        2:"happy",
        3:"neutral",
        4:"sad",
        5:"angry",
        6:"sick",
        7:"cool",
        8:"love",
        9:"sleepy",
        10:"busy"
    }

    current_nickname = ""

    addFriend_signal = pyqtSignal(str)
    userStatus_changed = pyqtSignal(str) 
    userNickname_changed = pyqtSignal(str) 
    friendSelected = pyqtSignal(str, str)
    recoverRequest_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.initUI()

    def set_slave(self, slave_window):
        self.slave = slave_window

    def closeEvent(self, event):
        if hasattr(self, 'slave'):
            self.slave.close()
        QApplication.quit() # Завершает цикл обработки событий Qt
        super().closeEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.slave.showMinimized()
            elif self.isMaximized():
                self.slave.showMaximized()
            else:
                self.slave.showNormal()
        super().changeEvent(event)

    def event(self, event):
        if event.type() == QEvent.WindowActivate:
            # Поднимаем второе окно, но не забираем фокус надолго
            self.slave.raise_()
            self.raise_() 
        return super().event(event)

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

    def mousePressEvent(self, event):
        if self.recoverMenu_process_indicator_label.pixmap() != self.recoverMenu_process_indicator_pix["loading"]:
            if not self.status_menu.isHidden():
                # Если клик был НЕ по меню статуса
                if not self.status_menu.geometry().contains(event.pos()):
                    self.status_menu.hide()
            
            elif not self.recover_menu.isHidden():
                if not self.recover_menu.geometry().contains(event.pos()):
                    self.recover_menu.hide()
            
            super().mousePressEvent(event)

    def toggle_status_menu(self):
        if self.recoverMenu_process_indicator_label.pixmap() != self.recoverMenu_process_indicator_pix["loading"]:
            if self.status_menu.isHidden():
                self.status_menu.show()
                self.status_menu.raise_() # Выводим на передний план
                self.recover_menu.hide()
            else:
                self.status_menu.hide()

    def set_new_status(self, status):
        self.selectedStatus = status
        self.status_icon_label.setPixmap(self.status_icon_pix[self.selectedStatus])
        self.selectStatus_highlight_label.setGeometry(self.selectedStatusMenu.get(self.selectedStatus)[0], self.selectedStatusMenu.get(self.selectedStatus)[1], self.selectStatus_status_highlight_pix.width(), self.selectStatus_status_highlight_pix.height())
        self.status_menu.hide()
        self.userStatusChanged()

    def toggle_recovery_menu(self):
        if self.recoverMenu_process_indicator_label.pixmap() != self.recoverMenu_process_indicator_pix["loading"]:
            if self.recover_menu.isHidden():
                self.recover_menu.show()
                self.recover_menu.raise_() # Выводим на передний план
                self.status_menu.hide()
            else:
                self.recover_menu.hide()

    def recover_request(self):
        friend_code = self.recoverMenu_friendCode_entry.text().strip()
        if friend_code:
            self.recoverMenu_process_indicator_label.setPixmap(self.recoverMenu_process_indicator_pix["loading"])
            self.recoverRequest_signal.emit(friend_code)
                
    def recovery_get_answer(self, result):
        if result:
            self.recoverMenu_process_indicator_label.setPixmap(self.recoverMenu_process_indicator_pix["confirmed"])
        else:
            self.recoverMenu_process_indicator_label.setPixmap(self.recoverMenu_process_indicator_pix["denied"])

    def on_custom_scroll_moved(self, value_pct):
        """Когда тянем ползунок (value_pct теперь всегда 0..100)"""
        vbar = self.vbar
        max_scroll = vbar.maximum()
        if max_scroll > 0:
            # Просто применяем процент к максимальному значению прокрутки
            new_scroll_pos = int((value_pct / 100) * max_scroll)
            vbar.setValue(new_scroll_pos)

    def on_vbar_moved(self, value):
        """Когда список крутится колесиком или кнопками"""
        max_scroll = self.vbar.maximum()
        if max_scroll > 0:
            # Переводим текущую позицию списка в проценты
            current_pct = int((value / max_scroll) * 100)
            
            # Двигаем визуальный ползунок без вызова обратных сигналов
            self.scrollbar_point.blockSignals(True)
            self.scrollbar_point.setValue(current_pct)
            self.scrollbar_point.blockSignals(False)        

    def update_contacts_list(self, contacts):
        """Функция для заполнения списка (вызывать при получении данных от сервера)"""
        # Очистка
        for i in reversed(range(self.scroll_layout.count())): 
            self.scroll_layout.itemAt(i).widget().setParent(None)

        # Добавление
        for c in contacts:
            nickname = c[0]
            status = self.contacts_status_icon_pix[self.statusCodesToNames.get(c[1], "offline")]
            friendCode = c[2]
            item = ContactItem(nickname, status, friendCode, parent=self.scroll_content)
            item.clicked.connect(lambda nick, it=item: self.handle_contact_clicked(it))
            self.scroll_layout.addWidget(item)

    def handle_contact_clicked(self, clicked_item):
        if self.selectedContact != None:
            self.selectedContact.set_selected(False)

        clicked_item.set_selected(True)
        self.selectedContact = clicked_item
        self.friendSelected.emit(clicked_item.nickname, clicked_item.friendCode)

    def add_friend(self):
        friend_code = self.addFriend_entry.text().strip()
        if friend_code:
            self.addFriend_signal.emit(friend_code)
            self.addFriend_entry.clear()

    def load_user_data(self, data):
        self.nickname_entry.setText(data.get("nickname", ""))
        self.friend_code_display.setText(data.get("friendCode", ""))
        # Устанавливаем иконку статуса согласно сохраненному значению
        self.update_status_icon(data.get("status", 1))

    def setFriendCode(self, friendCode):
        self.friend_code_display.setText(friendCode)

    def userNicknameChanged(self):
        nickname = self.current_nickname
        if self.nickname_entry.text().strip() != self.current_nickname:
            nickname = self.nickname_entry.text().strip()
            self.current_nickname = nickname
        self.userNickname_changed.emit(nickname)

    def userStatusChanged(self):
        status = self.selectedStatus
        self.userStatus_changed.emit(status)

    def eventFilter(self, watched, event):
        # Если событие происходит в поле ника и это потеря фокуса
        if watched == self.nickname_entry and event.type() == QEvent.FocusOut:
            self.userNicknameChanged()
        return super().eventFilter(watched, event)

    def setUserNickname(self,nickname):
        self.current_nickname = nickname
        self.nickname_entry.setText(nickname)

    def initUI(self):

        self.setWindowTitle(" ")
        self.setFixedSize(339, 600)
        self.setWindowIcon(QIcon(imagePath + "/icon.png"))

        self.central = QWidget()
        self.setCentralWidget(self.central)

        #загрузка картинок
        bg_pix = QPixmap(imagePath + "/background.png")
        
        userInfo_bg_pix = QPixmap(imagePath + "/userInfo_bg.png")
        userNickname_bg_pix = QPixmap(imagePath + "/userNickname_bg.png")
        self.status_icon_pix = {
            "joy": QPixmap(imagePath + "/statusJoyX3.png"),
            "happy": QPixmap(imagePath + "/statusHappyX3.png"),
            "neutral": QPixmap(imagePath + "/statusNeutralX3.png"),
            "sad": QPixmap(imagePath + "/statusSadX3.png"),
            "angry": QPixmap(imagePath + "/statusAngryX3.png"),
            "sick": QPixmap(imagePath + "/statusSickX3.png"),
            "cool": QPixmap(imagePath + "/statusCoolX3.png"),
            "love": QPixmap(imagePath + "/statusLoveX3.png"),
            "sleepy": QPixmap(imagePath + "/statusSleepyX3.png"),
            "busy": QPixmap(imagePath + "/statusBusyX3.png"),
        }
        friednCode_bg_pix = QPixmap(imagePath + "/friendCode_bg.png")

        selectStatus_bg_pix = QPixmap(imagePath + "/selectStatus_bg.png")
        self.selectStatus_status_highlight_pix = QPixmap(imagePath + "/selectStatus_highlight.png")
        selectStatus_statuses_pix = QPixmap(imagePath + "/selectStatus_statuses.png")
        selectStatus_window_highlight_pix = QPixmap(imagePath + "/selectStatus_window_highlight.png")

        recoverMenu_bg_pix = QPixmap(imagePath + "/recoverMenu_bg.png")
        recoverMenu_friendCode_entry_bg_pix = QPixmap(imagePath + "/recoverMenu_friendCode_entry_bg.png")
        
        self.recoverMenu_process_indicator_pix = {
            "idle": QPixmap(imagePath + "/recoverMenu_process_indicator_idle.png"),
            "loading": QPixmap(imagePath + "/recoverMenu_process_indicator_loading.png"),
            "confirmed": QPixmap(imagePath + "/recoverMenu_process_indicator_confirmed.png"),
            "denied": QPixmap(imagePath + "/recoverMenu_process_indicator_denied.png"),
        }
        recoverMenu_window_highlight_pix = QPixmap(imagePath + "/recoverMenu_window_highlight.png")

        contacts_list_bg_pix = QPixmap(imagePath + "/contactsList_bg.png")
        scrollbar_bg_pix = QPixmap(imagePath + "/scrollbar_bg.png")
        scrollbar_point_pix = QPixmap(imagePath + "/scroll.png")
        
        self.contacts_status_icon_pix = {
            "joy": QPixmap(imagePath + "/statusJoyX1.png"),
            "happy": QPixmap(imagePath + "/statusHappyX1.png"),
            "neutral": QPixmap(imagePath + "/statusNeutralX1.png"),
            "sad": QPixmap(imagePath + "/statusSadX1.png"),
            "angry": QPixmap(imagePath + "/statusAngryX1.png"),
            "sick": QPixmap(imagePath + "/statusSickX1.png"),
            "cool": QPixmap(imagePath + "/statusCoolX1.png"),
            "love": QPixmap(imagePath + "/statusLoveX1.png"),
            "sleepy": QPixmap(imagePath + "/statusSleepyX1.png"),
            "busy": QPixmap(imagePath + "/statusBusyX1.png"),
            "offline": QPixmap(imagePath + "/statusOfflineX1.png"),
        }

        contact_select_highlight_pix = QPixmap(imagePath + "/contact_select_highlight.png")

        contacts_window_highlight_pix = QPixmap(imagePath + "/contacts_window_highlight.png")
        
        addFriend_bg_pix = QPixmap(imagePath + "/addFriend_bg.png")
        addFriend_entry_bg_pix = QPixmap(imagePath + "/addFriend_entry_bg.png")
        
        recoverBtnPath = {
            "idle":imagePath + "/recoverBtnIdle.png",
            "hower": imagePath + "/recoverBtnHower.png",
            "pressed":imagePath + "/recoverBtnPressed.png" 
            }
        
        goBackBtnPath = {
            "idle": imagePath + "/goBackBtnIdle.png",
            "hower": imagePath + "/goBackBtnHower.png",
            "pressed":imagePath + "/goBackBtnPressed.png"
        }

        confirmBtnPath = {
            "idle": imagePath + "/confirmBtnIdle.png",
            "hower": imagePath + "/confirmBtnHower.png",
            "pressed": imagePath + "/confirmBtnPressed.png"
        }

        addFriendBtnPath = {
            "idle": imagePath + "/addBtnIdle.png",
            'hower': imagePath + "/addBtnHower.png",
            'pressed': imagePath + "/addBtnPressed.png"
        }




        font = QFont("Ubuntu", 10)
        font.setWeight(60) 

        #фон окна
        self.bg_label = QLabel(self.central)
        self.bg_label.setPixmap(bg_pix)
        self.bg_label.setGeometry(0, 0, 339, 600)

        #Блок user info

            #фон + блик
        
        user_info_bg_label = QLabel(self.central)
        user_info_bg_label.setPixmap(userInfo_bg_pix)
        user_info_bg_label.setGeometry(24, 0, userInfo_bg_pix.width(), userInfo_bg_pix.height())

            #Надпись You are:

        youAre_label = QLabel("You are:", self.central)
        youAre_label.setFont(font)
        youAre_label.setGeometry(62, 24, 100, 20)
        youAre_label.setStyleSheet("color: #3C4A25;")
        
            #Поле ввода ника

        nickname_entry_bg_label = QLabel(self.central)
        nickname_entry_bg_label.setPixmap(userNickname_bg_pix)
        nickname_entry_bg_label.setGeometry(50, 40, userNickname_bg_pix.width(), userNickname_bg_pix.height())

        self.nickname_entry = QLineEdit(self.central)
        self.nickname_entry.setGeometry(67, 43, 120, 30)
        self.nickname_entry.setStyleSheet("background: transparent; border: none; color: #3C4A25") 
        self.nickname_entry.setFont(QFont("Ubuntu", pointSize=10, weight=4000))
        self.nickname_entry.installEventFilter(self)
        self.nickname_entry.returnPressed.connect(self.userNicknameChanged)
        self.nickname_entry.setPlaceholderText("Your nickname")

            #Иконка статуса
        
        self.status_icon_label = QLabel(self.central)
        self.status_icon_label.setPixmap(self.status_icon_pix[self.selectedStatus])
        self.status_icon_label.setGeometry(210, 30, self.status_icon_pix[self.selectedStatus].width(), self.status_icon_pix[self.selectedStatus].height())

        self.status_icon_btn = QPushButton(self.central)
        self.status_icon_btn.setGeometry(210, 30, self.status_icon_pix[self.selectedStatus].width(), self.status_icon_pix[self.selectedStatus].height())
        self.status_icon_btn.setStyleSheet("background: transparent; border: none;")
        self.status_icon_btn.clicked.connect(self.toggle_status_menu)

            #Выпадающее окно с выбором статуса

        self.status_menu = QFrame(self.central)
        self.status_menu.setGeometry(100, 70, selectStatus_bg_pix.width(), selectStatus_bg_pix.height())
        self.status_menu.hide()

                #фон

        status_menu_bg_label = QLabel(self.status_menu)
        status_menu_bg_label.setPixmap(selectStatus_bg_pix)
        status_menu_bg_label.setGeometry(0, 0, selectStatus_bg_pix.width(), selectStatus_bg_pix.height())

                #статусы

        self.selectStatus_highlight_label = QLabel(self.status_menu)
        self.selectStatus_highlight_label.setPixmap(self.selectStatus_status_highlight_pix)
        self.selectStatus_highlight_label.setGeometry(self.selectedStatusMenu.get(self.selectedStatus)[0], self.selectedStatusMenu.get(self.selectedStatus)[1], self.selectStatus_status_highlight_pix.width(), self.selectStatus_status_highlight_pix.height())

        statuses_label = QLabel(self.status_menu)
        statuses_label.setPixmap(selectStatus_statuses_pix)
        statuses_label.setGeometry(31, 33, selectStatus_statuses_pix.width(), selectStatus_statuses_pix.height())

        selectStatusBtns = []
        for status, pos in self.selectedStatusMenu.items():
            btn = QPushButton(self.status_menu)
            btn.setGeometry(pos[0], pos[1], self.selectStatus_status_highlight_pix.width(), self.selectStatus_status_highlight_pix.height())
            selectStatusBtns.append(btn)
            btn.setStyleSheet("background: transparent; border: none;")
            btn.clicked.connect(lambda _, st=status: self.set_new_status(st))

                #блик

        status_menu_window_highlight_label = QLabel(self.status_menu)
        status_menu_window_highlight_label.setPixmap(selectStatus_window_highlight_pix)
        status_menu_window_highlight_label.setGeometry(13, 30, selectStatus_window_highlight_pix.width(), selectStatus_window_highlight_pix.height())
        status_menu_window_highlight_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            
            #надпись Your friend-code:

        friendCode_label = QLabel("Your friend-code:", self.central)
        friendCode_label.setFont(font)
        friendCode_label.setGeometry(62, 83, 150, 20)
        friendCode_label.setStyleSheet("color: #3C4A25;")

            #поле с френд кодом (нельзя писать)

        friendCode_text_bg_label = QLabel(self.central)
        friendCode_text_bg_label.setPixmap(friednCode_bg_pix)
        friendCode_text_bg_label.setGeometry(50, 100, friednCode_bg_pix.width(), friednCode_bg_pix.height())

        self.friend_code_display = QTextEdit(self.central)
        self.friend_code_display.setReadOnly(True)
        self.friend_code_display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.friend_code_display.setStyleSheet("background: transparent; border: none; color: #3C4A25") 
        self.friend_code_display.setFont(QFont("Ubuntu", pointSize=10, weight=4000))
        self.friend_code_display.setGeometry(67, 107, 170, 30)

            #кнопка открытия меню восстановления

        self.recover_menu_btn = QPushButton(self.central)
        self.recover_menu_btn.setGeometry(238, 107, 32, 32)
        self.recover_menu_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                image: url({recoverBtnPath['idle'].replace('\\', '/')});
            }}
            QPushButton:hover {{
                image: url({recoverBtnPath['hower'].replace('\\', '/')});
            }}
            QPushButton:pressed {{
                image: url({recoverBtnPath['pressed'].replace('\\', '/')});
            }}
        """) 
        self.recover_menu_btn.clicked.connect(self.toggle_recovery_menu)

            #меню восстановления

        self.recover_menu = QFrame(self.central)
        self.recover_menu.setGeometry(40, 115, recoverMenu_bg_pix.width(), recoverMenu_bg_pix.height())
        self.recover_menu.hide()

                #фон

        recover_menu_bg_label = QLabel(self.recover_menu)
        recover_menu_bg_label.setPixmap(recoverMenu_bg_pix)
        recover_menu_bg_label.setGeometry(0, 0, recoverMenu_bg_pix.width(), recoverMenu_bg_pix.height())

                #кнопка назад

        self.recover_menu_back_btn = QPushButton(self.recover_menu)
        self.recover_menu_back_btn.setGeometry(30, 30, 32, 32)
        self.recover_menu_back_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                image: url({goBackBtnPath['idle'].replace('\\', '/')});
            }}
            QPushButton:hover {{
                image: url({goBackBtnPath['hower'].replace('\\', '/')});
            }}
            QPushButton:pressed {{
                image: url({goBackBtnPath['pressed'].replace('\\', '/')});
            }}
        """) 
        self.recover_menu_back_btn.clicked.connect(self.toggle_recovery_menu)

                #надпись Account recovery

        recoverMenu_label = QLabel("Account recovery", self.recover_menu)
        recoverMenu_label.setFont(QFont("Ubuntu", pointSize=10, weight=4000))
        recoverMenu_label.setGeometry(90, 30, 200, 30)
        recoverMenu_label.setStyleSheet("color: #3C4A25;")

                #надпись Enter friend-code:

        recoverMenu_friendCode_label = QLabel("Enter friend-code:", self.recover_menu)
        recoverMenu_friendCode_label.setFont(QFont("Ubuntu", pointSize=10, weight=4000))
        recoverMenu_friendCode_label.setGeometry(64, 60, 150, 30)
        recoverMenu_friendCode_label.setStyleSheet("color: #3C4A25;")

                #поле ввода friend code

        self.recoverMenu_friendCode_entry_bg_label = QLabel(self.recover_menu)
        self.recoverMenu_friendCode_entry_bg_label.setPixmap(recoverMenu_friendCode_entry_bg_pix)
        self.recoverMenu_friendCode_entry_bg_label.setGeometry(50, 80, recoverMenu_friendCode_entry_bg_pix.width(), recoverMenu_friendCode_entry_bg_pix.height())

        self.recoverMenu_friendCode_entry = QLineEdit(self.recover_menu)
        self.recoverMenu_friendCode_entry.setGeometry(67, 83, 150, 30)
        self.recoverMenu_friendCode_entry.setStyleSheet("background: transparent; border: none; color: #3C4A25")
        self.recoverMenu_friendCode_entry.setFont(QFont("Ubuntu", pointSize=10, weight=4000))
        self.recoverMenu_friendCode_entry.setPlaceholderText("A1B2-C3D4-E5F6-G7H8")

                #кнопка подтверждения

        self.recoverMenu_confirm_btn = QPushButton(self.recover_menu)
        self.recoverMenu_confirm_btn.setGeometry(95, 115, 90, 32)
        self.recoverMenu_confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                image: url({confirmBtnPath['idle'].replace('\\', '/')});
            }}
            QPushButton:hover {{
                image: url({confirmBtnPath['hower'].replace('\\', '/')});
            }}
            QPushButton:pressed {{
                image: url({confirmBtnPath['pressed'].replace('\\', '/')});
            }}
        """) 
        self.recoverMenu_confirm_btn.clicked.connect(lambda: self.recover_request())

                #индикатор процесса подтверждения

        self.recoverMenu_process_indicator_label = QLabel(self.recover_menu)
        self.recoverMenu_process_indicator_label.setPixmap(self.recoverMenu_process_indicator_pix["idle"])
        self.recoverMenu_process_indicator_label.setGeometry(190, 114, self.recoverMenu_process_indicator_pix["idle"].width(), self.recoverMenu_process_indicator_pix["idle"].height())

                #блик

        recover_menu_window_highlight_label = QLabel(self.recover_menu)
        recover_menu_window_highlight_label.setPixmap(recoverMenu_window_highlight_pix)
        recover_menu_window_highlight_label.setGeometry(15, 30, recoverMenu_window_highlight_pix.width(), recoverMenu_window_highlight_pix.height())
        recover_menu_window_highlight_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        #блок список контактов

            #фон

        contacts_bg_label = QLabel(self.central)
        contacts_bg_label.setPixmap(contacts_list_bg_pix)
        contacts_bg_label.setGeometry(27, 135, contacts_list_bg_pix.width(), contacts_list_bg_pix.height())

            #Прокручиваемый список контактов

        # --- Настройка области прокрутки ---
        self.scroll_area = QScrollArea(self.central)
        self.scroll_area.setGeometry(54, 170, 220, 300) 
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        # Контейнер для виджетов
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(2) # Расстояние между контактами
        self.scroll_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.scroll_content)

        # Связываем со стандартным скроллбаром (невидимым)
        self.vbar = self.scroll_area.verticalScrollBar()
        self.vbar.valueChanged.connect(self.on_vbar_moved)

        #фон скроллбара
        scrollbar_bg_label = QLabel(self.central)
        scrollbar_bg_label.setPixmap(scrollbar_bg_pix)
        scrollbar_bg_label.setGeometry(233, 148, scrollbar_bg_pix.width(), scrollbar_bg_pix.height())

        #ползунок 
        self.scrollbar_point = scrollbar_point_widget(self.central)
        self.scrollbar_point.valueChanged.connect(self.on_custom_scroll_moved)
        self.scrollbar_point.move(257, 173)

        # Фильтр событий, чтобы колесико мыши работало
        self.scroll_area.installEventFilter(self.scrollbar_point)


            #блик

        contacts_window_highlight_label = QLabel(self.central)
        contacts_window_highlight_label.setPixmap(contacts_window_highlight_pix)
        contacts_window_highlight_label.setGeometry(45, 165, contacts_window_highlight_pix.width(), contacts_window_highlight_pix.height())
        contacts_window_highlight_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        #блок добавления в друзья

            #фон + блик

        addFriend_bg_label = QLabel(self.central)
        addFriend_bg_label.setPixmap(addFriend_bg_pix)
        addFriend_bg_label.setGeometry(24, 469, addFriend_bg_pix.width(), addFriend_bg_pix.height())

            #надпись Friend's code:

        addFriend_label = QLabel("Friend's code:", self.central)
        addFriend_label.setFont(font)   
        addFriend_label.setGeometry(69, 500, 150, 20)
        addFriend_label.setStyleSheet("color: #3C4A25;")

            #поле ввода friend code

        addFriend_entry_bg_label = QLabel(self.central)
        addFriend_entry_bg_label.setPixmap(addFriend_entry_bg_pix)
        addFriend_entry_bg_label.setGeometry(58, 517, addFriend_entry_bg_pix.width(), addFriend_entry_bg_pix.height())

        self.addFriend_entry = QLineEdit(self.central)
        self.addFriend_entry.setGeometry(76, 521, 155, 30)
        self.addFriend_entry.setStyleSheet("background: transparent; border: none; color: #3C4A25")
        self.addFriend_entry.setFont(QFont("Ubuntu", pointSize=10, weight=4000))
        self.addFriend_entry.setPlaceholderText("A1B2-C3D4-E56-G7H8")

            #кнопка добавления

        self.addFriend_btn = QPushButton(self.central)
        self.addFriend_btn.setGeometry(246, 521, 32, 32)
        self.addFriend_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                image: url({addFriendBtnPath['idle'].replace('\\', '/')});
            }}
            QPushButton:hover {{
                image: url({addFriendBtnPath['hower'].replace('\\', '/')});
            }}
            QPushButton:pressed {{
                image: url({addFriendBtnPath['pressed'].replace('\\', '/')});
            }}
        """) 
        self.addFriend_btn.clicked.connect(lambda: self.add_friend())

        self.setFocus()
    