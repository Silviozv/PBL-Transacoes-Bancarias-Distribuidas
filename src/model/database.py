import threading
import socket
import requests
import time
from model.lamport_clock import Lamport_clock

class Database:
    accounts: dict
    users: dict
    ip_bank: str
    lock: object

    def __init__(self):
        self.ip_bank = socket.gethostbyname(socket.gethostname())

        self.banks = [self.ip_bank]
        self.banks_recconection = {self.ip_bank: False}
        self.accounts = {}
        self.users = {}

        self.count_accounts = 0
        self.clock = Lamport_clock()
        self.leader = self.ip_bank
        self.flag_election = False

        self.lock = threading.Lock()

    def add_bank(self, ip_bank: str):
        with self.lock:
            self.banks.append(ip_bank)
            self.banks_recconection[ip_bank] = False

    def find_account(self, cpf: str, id: str) -> object:
        list_accounts = self.accounts[cpf]

        account = None
        for i in range(len(list_accounts)):
            if list_accounts[i].id == id:
                account = list_accounts[i]

        return account

    def find_priority_bank(self) -> str:
        ip_bank = ""
        for i in range(len(self.banks)):
            number = int(self.banks[i].replace(".", ""))
            if ip_bank == "":
                lower_number = number
                ip_bank = self.banks[i]
            elif number < lower_number:
                lower_number = number
                ip_bank = self.banks[i]

        return ip_bank

    def check_connections(self):
        for i in range(len(self.banks)):
            try:
                url = (f"http://{self.banks[i]}:5070/")
                requests.head(url)
            except (requests.exceptions.ConnectionError) as e:
                self.banks_recconection[self.banks[i]] = True
                threading.Thread( target=self.loop_reconnection(), args=(self.banks[i])).start()

    def loop_reconnection(self, ip_bank: str):
        loop = True
        while loop == True:
            try:
                url = (f"http://{ip_bank}:5070/")
                requests.head(url)
                loop = False
                self.banks_recconection[self.banks[i]] = False
            except (requests.exceptions.ConnectionError) as e:
                time.sleep(2.5)
