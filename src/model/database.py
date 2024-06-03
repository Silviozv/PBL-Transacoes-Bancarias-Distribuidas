import threading
import socket

class Database:
    accounts: dict
    users: dict
    ip_bank: str
    lock: object

    def __init__(self):
        self.accounts = {}
        self.users = {}

        self.ip_bank = socket.gethostbyname(socket.gethostname())

        self.lock = threading.Lock()

    def find_account_by_key(self, key: str) -> dict:
        data_search = {"Conta encontrada": False}

        for id in self.accounts.keys():
            if self.accounts[id].key == key:
                data_search["ID conta"] = id
                data_search["Conta encontrada"] = True

        return data_search