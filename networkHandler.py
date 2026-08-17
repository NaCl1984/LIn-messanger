import socket
import os
import json
import threading
import queue
import time
from PyQt5.QtCore import QObject, pyqtSignal
import requests


GITHUB_VERSION_RAW = "https://raw.githubusercontent.com/NaCl1984/LIn-messanger/refs/heads/main/version.json"
GITHUB_LATEST_VERSION = "https://github.com/NaCl1984/LIn-messanger/releases/latest/download/LInM.exe"

currentServerIp = "lin-domen.giize.com"
currentPort = 8888

VERSION = "2.2.2"



class NetworkManager(QObject):
    # Создаем сигналы для общения с GUI
    message_received = pyqtSignal(dict)    # Для типа 'msg'
    contacts_received = pyqtSignal(list)   # Для типа 'sendContacts'
    history_received = pyqtSignal(list)    # Для типа 'sendHistory'
    my_code_received = pyqtSignal(str)     # Для типа 'sendFriendCode'
    connectAbort_signal = pyqtSignal()
    recoverAnswer_signal = pyqtSignal(bool)
    auth_answer_signal = pyqtSignal(bool)
    updateRequired_signal = pyqtSignal(dict)
    isConnect = False

    statusStrToInt = {
        "joy":1,
        "happy":2,
        "neutral":3,
        "sad":4,
        "angry":5,
        "sick":6,
        "cool":7,
        "love":8,
        "sleepy":9,
        "busy":10
    }

    def __init__(self, USER_INFO_PATH):
        super().__init__()
        self.USER_INFO_PATH = USER_INFO_PATH
        # ... остальная инициализация ...

    def onClose(self):
        try:
            self.client_socket.sendall(json.dumps({"type":"disconnect"}, ensure_ascii=False).encode("utf-8"))
        except:
            pass
        try:
            self.client_socket.close()
        except:
            pass

    def update_version_from_github(self):
        try:
            response = requests.get(GITHUB_VERSION_RAW, timeout=5)
            if response.status_code == 200:
                # ПРЕОБРАЗУЕМ ТЕКСТ В СЛОВАРЬ
                data = response.json() 
                
                # Извлекаем значения из полученного JSON
                new_latest = data.get("latest")
                new_critical = data.get("critical")

                # Обновляем, если версия изменилась
                if new_latest and new_latest != VERSION:
                    if new_critical and new_critical != VERSION:
                        self.updateRequired_signal.emit({"type":"updateRequired", "critical":True , "link":GITHUB_LATEST_VERSION})
                    else:
                        self.updateRequired_signal.emit({"type":"updateRequired", "critical":False , "link":GITHUB_LATEST_VERSION})

        except Exception as e:
            print(f"Ошибка проверки версии на GitHub: {e}")

    

    def receive_loop(self):
        global currentServerIp, currentPort
        max_reconnect_attempts = 5
        attempts_with_same_address = 0

        while True:
            try:
                self.update_version_from_github()
                print(f"Подключение к серверу {currentServerIp}:{currentPort}...")
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((currentServerIp, currentPort))
                
                self.isConnect = True
                self.sendHandshake() 

                buffer = ""
                while True:
                    try:
                        chunk = self.client_socket.recv(4096)  
                        if not chunk:
                            break
                        buffer += chunk.decode()
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            if not line.strip():
                                continue
                            msg_obj = json.loads(line)
                            data_type = msg_obj.get("type")
                            
                            if data_type == "msg":
                                self.message_received.emit(msg_obj) 
                            elif data_type == "sendContacts":
                                self.contacts_received.emit(msg_obj.get("contacts"))
                            elif data_type == "sendHistory":
                                self.history_received.emit(msg_obj.get("messages"))
                            elif data_type == "sendFriendCode":
                                self.my_code_received.emit(msg_obj.get("friendCode"))
                            elif data_type == "recoverAnswer":
                                self.recoverAnswer_signal.emit(msg_obj.get("answer"))
                            elif data_type == "authAnswer":
                                self.auth_answer_signal.emit(msg_obj.get("answer"))
                            elif data_type == "updateRequired":
                                self.updateRequired_signal.emit(msg_obj)
                                break

                    except (ConnectionResetError, ConnectionAbortedError, socket.timeout) as e:     
                        print(f"Ошибка в цикле приема: {e}")
                        self.connectAbort_signal.emit()
                        break
                    except Exception as e:
                        print(f"Ошибка в цикле приема: {e}")
                        self.connectAbort_signal.emit()
                        break
                self.connectAbort_signal.emit() 
                self.isConnect = False

            except Exception as e:
                print(f"Ошибка подключения к {currentServerIp}:{currentPort}: {e}")
            
            # --- Логика после разрыва или неудачного подключения ---
            try:
                self.client_socket.close()
            except:
                pass

            attempts_with_same_address += 1
            if attempts_with_same_address >= max_reconnect_attempts:
                print(f"Достигнут лимит попыток ({max_reconnect_attempts})")
                self.isConnect = False
                self.connectAbort_signal.emit()
                break
            
            print(f"Повторная попытка подключения через 10 секунд...")
            import time
            time.sleep(10)

    def getUserInfo(self):
        try:
            if not os.path.exists(self.USER_INFO_PATH) or os.path.getsize(self.USER_INFO_PATH) == 0:
                return {"nickname": "User", "status": 1, "friendCode": "", "uuid":""}
                
            with open(self.USER_INFO_PATH, "r", encoding="utf-8") as file:
                data = file.read().strip()
                if not data:
                    return {"nickname": "User", "status": 1, "friendCode":"", "uuid":""}
                return json.loads(data)
        except Exception:
            return {"nickname": "User", "status": 1, "friendCode":"", "uuid":""}

    def send_packet(self, packet_dict):
        if self.isConnect: # Проверка флага соединения
            try:
                json_data = json.dumps(packet_dict, ensure_ascii=False)
                self.client_socket.sendall((json_data + "\n").encode("utf-8"))
            except Exception as e:
                print(f"Ошибка отправки: {e}")

    def requestHistory(self, friendCode):
        self.send_packet({"type": "requestHistory", "friendCode": friendCode})

    def addFriend(self, friendCode):
        self.send_packet({"type": "addFriend", "friendCode": friendCode})

    def updateStatus(self, status):
        self.send_packet({"type": "updateStatus", "status": self.statusStrToInt.get(status, 1)}) 

    def updateNickname(self, nickname):
        self.send_packet({"type": "updateNickname", "nickname": nickname})

    def sendMessage(self, text, receiverCode):
        self.send_packet({
            "type": "msg",
            "text": text,
            "receiverCode": receiverCode
        })

    def requestRecover(self, friendCode):
        self.send_packet({"type": "requestRecover", "friendCode": friendCode})

    def sendHandshake(self):
        userInfo = self.getUserInfo()
        self.send_packet({
            "type":"handShake", 
            "friendCode": userInfo.get("friendCode"), 
            "nickname": userInfo.get("nickname"), 
            "status": self.statusStrToInt.get(userInfo.get("status"), 1),
            "uuid":userInfo.get("uuid"),
            "version":VERSION
            }) 