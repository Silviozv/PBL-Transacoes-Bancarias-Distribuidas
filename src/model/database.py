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
        self.packages = {}

        self.token = False
        self.token_start_pass = False
        self.time_token = 0
        self.lamport_clock = Lamport_clock()

        #self.count_accounts = 0
        #self.clock = Lamport_clock()
        #self.leader = self.ip_bank
        #self.flag_election = False

        self.lock = threading.Lock()

    def add_bank(self, ip_bank: str):
        with self.lock:
            self.banks.append(ip_bank)
            self.banks_recconection[ip_bank] = False

    def count_banks_on(self):
        count = 0
        for ip in self.banks_recconection.keys():
            if ip != self.ip_bank and self.banks_recconection[ip] == False:
                count += 1

        return count

    def sort_ip_banks(self):
        for i in range(1, len(self.banks)):
            insert_index = i
            current_value = self.banks.pop(i)
            for j in range(i - 1, -1, -1):
                if int(self.banks[j].replace(".","")) > int(current_value.replace(".","")):
                    insert_index = j
            self.banks.insert(insert_index, current_value)

    def find_next_bank(self):
        next_bank = ""
        for i in range(len(self.banks)):
            if self.banks[i] == self.ip_bank:
                if i == (len(self.banks) - 1):
                    next_bank = self.banks[0]
                else:
                    next_bank = self.banks[i + 1]

        return next_bank

    def find_first_bank(self):
        next_bank = ""
        for i in range(len(self.banks)):
            if self.banks_recconection[self.banks[i]] == False and next_bank == "":
                next_bank = self.banks[i]

        return next_bank



    def find_account(self, cpf: str, id: str) -> object:
        list_accounts = self.accounts[cpf]

        account = None
        for i in range(len(list_accounts)):
            if list_accounts[i].id == id:
                account = list_accounts[i]

        return account

    '''
    def find_priority_bank(self) -> str:
        ip_bank = ""
        for i in range(len(self.banks)):
            if self.banks_recconection[self.banks[i]] == False:
                number = int(self.banks[i].replace(".", ""))
                if ip_bank == "":
                    lower_number = number
                    ip_bank = self.banks[i]
                elif number < lower_number:
                    lower_number = number
                    ip_bank = self.banks[i]

        return ip_bank
    '''

    def check_connections(self):
        for i in range(len(self.banks)):
            try:
                url = (f"http://{self.banks[i]}:5070/")
                requests.head(url)
            except (requests.exceptions.ConnectionError) as e:
                if self.banks_recconection[self.banks[i]] == False:
                    self.banks_recconection[self.banks[i]] = True
                    threading.Thread( target=self.loop_reconnection, args=(self.banks[i],)).start()

    def loop_reconnection(self, ip_bank: str):
        loop = True
        while loop == True:
            try:
                url = (f"http://{ip_bank}:5070/")
                requests.head(url)
                loop = False
                self.banks_recconection[ip_bank] = False
            except (requests.exceptions.ConnectionError) as e:
                time.sleep(2.5)

