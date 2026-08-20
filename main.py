import os
import json
from random import random
import threading
import queue
from pathlib import Path
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
import random

import requests
import chatGui
import socialGui
import authGui
import updateGui
import loadingGui
import networkHandler
import subprocess

def get_device_uuid():
    try:
        # Самый стабильный ID для Windows — UUID материнской платы/системы
        cmd = 'wmic csproduct get uuid'
        uuid = subprocess.check_output(cmd, shell=True).decode().split('\n')[1].strip()
        return uuid
    except Exception:
        # Запасной вариант по MAC-адресу, если wmic недоступен
        import uuid
        return str(uuid.getnode())

def get_data_path():
    if getattr(sys, 'frozen', False):
        appdata = os.getenv('APPDATA')
        if appdata:
            data_dir = os.path.join(appdata, 'LINMessenger')
        else:
            data_dir = os.path.dirname(sys.executable)
    else:
        data_dir = os.path.dirname(os.path.abspath(__file__))
    
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    return os.path.join(data_dir, 'userInfo.json')

USER_INFO_PATH = get_data_path()

if not os.path.exists(USER_INFO_PATH):
    with open(USER_INFO_PATH, "w", encoding="utf-8") as f:
        userData = {
            "nickname": f"User{random.randint(1000, 9999)}", 
            "status": "joy", 
            "friendCode": "", 
            "uuid":get_device_uuid(),
            "unreadContacts": []
            }
        json.dump(userData, f, ensure_ascii=False)
else:
    with open(USER_INFO_PATH, "r", encoding="utf-8") as f:
        userData = json.load(f)
        userData["uuid"] = get_device_uuid()
    with open(USER_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(userData, f, ensure_ascii=False)


isConnect = threading.Event()

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

chat_gui = chatGui.ChatWindow()
social_gui = socialGui.SocialWindow()
auth_gui = authGui.authWindow()
update_gui = updateGui.updateWindow()
loading_gui = loadingGui.loadingWindow()
net = networkHandler.NetworkManager(USER_INFO_PATH)

chat_gui.setParent(social_gui, Qt.Window) 
social_gui.set_slave(chat_gui)

chat_gui.USER_INFO_PATH = USER_INFO_PATH

selectedContact = None
recoverFriendCode = None



unread_contacts = [] 

def load_unread_contacts():
    global unread_contacts
    with open(USER_INFO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    unread_contacts = data.get("unreadContacts", [])
    return unread_contacts

def save_unread_contacts():
    with open(USER_INFO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["unreadContacts"] = unread_contacts
    with open(USER_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_unread_contact(friendCode):
    global unread_contacts
    if friendCode not in unread_contacts:
        unread_contacts.append(friendCode)
        save_unread_contacts()

def remove_unread_contact(friendCode):
    global unread_contacts
    if friendCode in unread_contacts:
        unread_contacts.remove(friendCode)
        save_unread_contacts()


unread_contacts = load_unread_contacts()



def load_unread_contacts():
    global unread_contacts
    with open(USER_INFO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    unread_contacts = data.get("unreadContacts", [])
    return unread_contacts

def save_unread_contacts():
    with open(USER_INFO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["unreadContacts"] = unread_contacts
    with open(USER_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def safeFriendCode(code):
    with open(USER_INFO_PATH, "r", encoding="utf-8") as f:
        userInfo = json.load(f)
    
    userInfo["friendCode"] = code
    
    with open(USER_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(userInfo, f, ensure_ascii=False, indent=4)

    social_gui.setFriendCode(code)

def getFriendCode():
    with open(USER_INFO_PATH, "r", encoding="utf-8") as f:
        userInfo = json.load(f)
    return userInfo.get("friendCode", "")

def updateUserNickname(nickname):
    with open(USER_INFO_PATH, "r", encoding="utf-8") as f:
        userInfo = json.load(f)
    
    userInfo["nickname"] = nickname
    
    with open(USER_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(userInfo, f, ensure_ascii=False)

    net.updateNickname(nickname)

def updateUserStatus(status):
    with open(USER_INFO_PATH, "r", encoding="utf-8") as f:
        userInfo = json.load(f)
    
    userInfo["status"] = status
    
    with open(USER_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(userInfo, f, ensure_ascii=False)

    net.updateStatus(status)

def changedSelectedContact(nickname, friendCode):
    global selectedContact
    net.requestHistory(friendCode)
    selectedContact = friendCode
    chat_gui.setContactNickname(nickname)
    remove_unread_contact(friendCode) 

def connected(contacts):
    social_gui.update_contacts_list(contacts)
    chat_gui.setStatusConnected()
    for friendCode in unread_contacts:
        social_gui.show_new_message_indicator(friendCode)

def recoverRequest(friendCode=getFriendCode()):
    net.requestRecover(friendCode)
    global recoverFriendCode
    recoverFriendCode = friendCode

def getRecoverAnswer(answer: bool):
    if answer:
        safeFriendCode(recoverFriendCode)
        net.sendHandshake()
    social_gui.recovery_get_answer(answer)

def handle_incoming_message(msg):
    # Проверяем, открыт ли сейчас чат с отправителем этого сообщения
    if msg.get("senderCode") == selectedContact:
        chat_gui.addMessage(msg)
    else:
        social_gui.show_new_message_indicator(msg.get("senderCode"))
        add_unread_contact(msg.get("senderCode"))
        
def auth_answer_proceed(answer):
    if answer and not update_gui.isVisible():
        social_gui.show()
        chat_gui.show()
        auth_gui.close()
        loading_gui.closeWithoutExit()
    elif not update_gui.isVisible():
        auth_gui.show()

def createNewAccount():
    safeFriendCode('')
    net.sendHandshake()

def connectAbort():
    loading_gui.closeWithoutExit()
    social_gui.show()
    chat_gui.show()
    chat_gui.setStatusNotConnected()

def start_update_process(download_url):
    try:
        if not getattr(sys, 'frozen', False):
            print("Тестовый запуск: обновление заблокировано, чтобы не заменить python.exe")
            return
        # 1. Определяем пути
        current_exe = sys.executable
        current_dir = os.path.dirname(current_exe)
        # Временный файл для новой версии
        temp_exe = os.path.join(current_dir, "update_new.exe")
        # Путь к bat-скрипту
        updater_bat = os.path.join(current_dir, "updater.bat")

        # 2. Скачиваем новый EXE
        response = requests.get(download_url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(temp_exe, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            print("Ошибка при скачивании файла")
            return

        # 3. Создаем BAT-скрипт для замены
        # %~nx0 — это имя самого батника для самоудаления
        # ping — это простая задержка в пару секунд, чтобы мессенджер успел закрыться
        bat_content = f"""@echo off
        taskkill /f /im "{os.path.basename(current_exe)}" >nul 2>&1
        ping 127.0.0.1 -n 3 >nul
        del /f /q "{current_exe}" 2>nul
        move /y "{temp_exe}" "{current_exe}" >nul 2>nul
        start "" "{current_exe}"
        del "%~f0" >nul 2>nul
        exit
        """.format(current_exe=current_exe, temp_exe=temp_exe)

        with open(updater_bat, "w", encoding="cp1251") as f:
            f.write(bat_content)

        # 4. Запускаем батник и выходим
        subprocess.Popen(f'start /min "" "{updater_bat}"', shell=True)
        sys.exit(0)

    except Exception as e:
        print(f"Критическая ошибка обновления: {e}")

def proceedUpdateRequired(dict):
    url = dict.get('link')
    isCritical = dict.get("critical")
    update_gui.display_update(url, isCritical, )
    auth_gui.close()
    social_gui.hide()
    chat_gui.hide()
    update_gui.show()

def updateLater():
    if isConnect.is_set():
        update_gui.close()
        loading_gui.closeWithoutExit()
        social_gui.show()
        chat_gui.show()
    
social_gui.setUserNickname(net.getUserInfo().get("nickname", ""))
social_gui.set_new_status(net.getUserInfo().get("status", "joy"))

# Подключаем сигналы 
net.my_code_received.connect(lambda msg: safeFriendCode(msg))
net.contacts_received.connect(lambda contacts: connected(contacts))
net.history_received.connect(lambda messages:  chat_gui.setChatHistory(messages))
net.connectAbort_signal.connect(connectAbort)
net.message_received.connect(handle_incoming_message)
net.recoverAnswer_signal.connect(getRecoverAnswer)
net.auth_answer_signal.connect(auth_answer_proceed)
net.updateRequired_signal.connect(proceedUpdateRequired)
net.loading_status_signal.connect(lambda msg: loading_gui.display_update(msg))
loading_gui.close_app_signal.connect(QApplication.quit)

loading_gui.show()

social_gui.setFriendCode(getFriendCode())

social_gui.userNickname_changed.connect(lambda nickname: updateUserNickname(nickname))
social_gui.userStatus_changed.connect(lambda status: updateUserStatus(status))
social_gui.addFriend_signal.connect(lambda code: net.addFriend(code))
social_gui.friendSelected.connect(lambda nickname, friendCode: changedSelectedContact(nickname, friendCode))
social_gui.recoverRequest_signal.connect(lambda friendCode: recoverRequest(friendCode))

chat_gui.sendMessage_signal.connect(lambda msg: net.sendMessage(msg, selectedContact))

auth_gui.linkDevice_signal.connect(recoverRequest)
auth_gui.createNewAccount_signal.connect(createNewAccount)

update_gui.update_signal.connect(start_update_process)
update_gui.updateLater_signal.connect(updateLater)

screen_geometry = app.desktop().screenGeometry()
x = (screen_geometry.width() - (social_gui.width() + chat_gui.width())) // 2 - 30
y = (screen_geometry.height() - social_gui.height()) // 2 - 50

social_gui.move(x, y)
chat_gui.move(x + social_gui.width() + (social_gui.width() // 10), y)

connectionThread = threading.Thread(target=net.receive_loop, daemon=True)
connectionThread.start()

sys.exit(app.exec_())