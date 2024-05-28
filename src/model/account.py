class Account:

    def __init__(self, type_account: str, names_user: list, cpfs: list):
        self.key = ""
        self.id = ""
        self.type_account = type_account
        self.names_user = names_user
        self.cpfs = cpfs
        self.balance = 0

    def set_id(self, id: str):
        self.id = id

    def set_key(self, key: str):
        self.key = key



