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

    def set_is_passing(self, is_passing: bool):
        with self.lock:
            self.is_passing = is_passing

    def set_time(self, time: int):
        with self.lock:
            self.time = time

    def set_id(self, id: str):
        with self.lock:
            self.current_id = id

    def reset_all_atributes(self):
        with self.lock:
            self.is_passing = False
            self.it_has = False
            self.time = 0
            self.current_id = None

    def create_token(self, ip_bank: str, banks: list) -> dict:
        date_time = datetime.now()
        id = (f"{ip_bank}{date_time.time()}{date_time.date()}")

        token_pass_counter = {}
        for i in range(len(banks)):
            token_pass_counter[banks[i]] = 0

        data_token = {"ID token": id, "Contadora de passagem do token": token_pass_counter, "Pacotes": []}

        return data_token


    def clear_token_pass_counter(self, token_pass_counter: dict):
        for key in token_pass_counter.keys():
            token_pass_counter[key] = 0