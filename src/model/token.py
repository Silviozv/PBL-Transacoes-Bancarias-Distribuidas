import threading
from datetime import datetime

class Token:

    def __init__(self):
        self.is_passing = False
        self.it_has = False
        self.time = 0
        self.current_id = None

        self.lock = threading.Lock()


    def set_it_has(self, it_has: bool):
        with self.lock:
            self.it_has = it_has
            print("Tenho o token: ", self.it_has)

    def set_is_passing(self, is_passing: bool):
        with self.lock:
            self.is_passing = is_passing
            print("Token setado para está passando.")

    def set_time(self, time: int):
        with self.lock:
            self.time = time

    def set_id(self, id: str):
        with self.lock:
            print("ID token: ", id)
            self.current_id = id


    def create_token(self, ip_bank: str) -> str:
        date_time = datetime.now()
        id = (f"{ip_bank}{date_time.time()}{date_time.date()}")
        return id


    def create_token_pass_counter(self, banks: list) -> dict:
        token_pass_counter = {}
        for i in range(len(banks)):
            token_pass_counter[banks[i]] = 0

        return token_pass_counter
    
    def clear_token_pass_counter(self, token_pass_counter: dict):
        for key in token_pass_counter.keys():
            token_pass_counter[key] = 0