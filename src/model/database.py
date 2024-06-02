import threading


class Database:
    accounts: dict
    users: dict

    def __init__(self):
        self.accounts = {}
        self.users = {}

        self.lock = threading.Lock()
