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

        self.count_accounts = 0

        self.ip_bank = socket.gethostbyname(socket.gethostname())
        self.lock = threading.Lock()

    def find_account(self, cpf: str, id: str) -> object:
        list_accounts = self.accounts[cpf]

        account = None
        for i in range(len(list_accounts)):
            if list_accounts[i].id == id:
                account = list_accounts[i]

        return account