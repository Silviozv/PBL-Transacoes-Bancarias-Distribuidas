import threading


class Account:
    key: str
    id: str
    type_account: list
    cpfs: list
    balance: float
    lock: object

    def __init__(self, data_account: dict):
        self.key = data_account["Chave"]  
        self.type_account = data_account["Tipo de conta"] 
        self.cpfs = data_account["CPFs"]  
        self.balance = 0
        self.blocked_balance = 0

        self.lock = threading.Lock()


    def deposit_balance(self, value: str) -> dict:
        with self.lock:
            self.balance += float(value)
        response = {"Bem sucedido": True}
        return response


    def withdraw_balance(self, value: str) -> dict:
        if self.balance >= float(value):
            response = {"Bem sucedido": True}
            with self.lock:
                self.balance -= float(value)
        else:
            response = {"Bem sucedido": False, "Justificativa": "Saldo insuficiente"}
        
        return response
        

    def deposit_blocked_balance(self, value: str) -> dict:
        with self.lock:
            self.blocked_balance += float(value)
        response = {"Bem sucedido": True}
        return response


    def withdraw_blocked_balance(self, value: str) -> dict:
        if self.blocked_balance >= float(value):
            response = {"Bem sucedido": True}
            with self.lock:
                self.blocked_balance -= float(value)
        else:
            response = {"Bem sucedido": False, "Justificativa": "Saldo reserva insuficiente"}
        
        return response
