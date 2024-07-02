import threading
import socket
import requests
from model.token import Token


class Database:
    accounts: dict
    users: dict
    ip_bank: str
    lock: object

    def __init__(self):
        ##
        self.port = "5080"
        ##
        self.ip_bank = socket.gethostbyname(socket.gethostname())
        #self.banks = [self.ip_bank]
        self.banks = [self.port]
        #self.banks_recconection = {self.ip_bank: False}
        self.banks_recconection = {self.port: False}
        self.index_actual_bank = None

        self.accounts = {}
        self.users = {}
        self.packages = {}

        self.ready_for_connection = False
        self.token = Token()
        self.token_problem_alert = False

        self.processing_package = False
        self.count_accounts = 0
        self.count_packages = 0

        self.lock = threading.Lock()


    def set_token_problem_alert(self, token_problem_alert: bool):
        with self.lock:
            self.token_problem_alert = token_problem_alert

    
    def add_bank(self, ip_bank: str):
        with self.lock:
            self.banks.append(ip_bank)
            self.banks_recconection[ip_bank] = False


    def add_account(self, account: object):
        with self.lock:
            self.count_accounts += 1
            self.accounts[account.key] = account


    def calculate_key(self) -> str:
        key = "AC" + str(self.count_accounts)
        return key


    def add_package(self, data_package: dict) -> int:
        id = self.count_packages
        with self.lock:
            self.packages[id] = {"Dados": data_package, "Terminado": False, "Bem sucedido": None, "Adicionado ao token": False}
            self.count_packages += 1

        return id


    def set_send_package_to_execution(self, id: str):
        with self.lock:
            self.packages[id]["Adicionado ao token"] = True


   
    def count_banks_on(self):
        count = 0
        for ip in self.banks_recconection.keys():
            #if ip != self.ip_bank and self.banks_recconection[ip] == False:
            if ip != self.port and self.banks_recconection[ip] == False:
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
        self.find_index_actual_bank()


    def find_index_actual_bank(self):
        for i in range(len(self.banks)):
            #if self.banks[i] == self.ip_bank:
            if self.banks[i] == self.port:
                self.index_actual_bank = i
                return

   
    def find_next_bank(self):
        next_bank = ""
        found = False
        index = self.index_actual_bank + 1

        if index == len(self.banks):
            index = 0

        while found == False:

            if index != self.index_actual_bank:

                if index == len(self.banks):
                    index = 0

                else:
                    if self.banks_recconection[self.banks[index]] == False:
                        try:
                            #url = (f"http://{self.banks[index]}:5070/ready_for_connection")
                            url = (f"http://{self.ip_bank}:{self.banks[index]}/ready_for_connection")
                            status_code = requests.get(url, timeout=5).status_code

                            if status_code == 200:
                                next_bank = self.banks[index]
                                found = True
                        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                            with self.lock:
                                self.banks_recconection[self.banks[index]] = True
                            threading.Thread(target=self.loop_reconnection, args=(self.banks[index],)).start()

                    index += 1

            else:
                found = True
                #next_bank = self.ip_bank
                next_bank = self.port
        return next_bank

   
    def find_first_bank(self):
        first_bank = ""
        found = False
        index = 0

        while found == False and index != len(self.banks):

            if index != self.index_actual_bank:
                if self.banks_recconection[self.banks[index]] == False:
                    try:
                        # url = (f"http://{self.banks[index]}:5070/ready_for_connection")
                        url = (f"http://{self.ip_bank}:{self.banks[index]}/ready_for_connection")
                        status_code = requests.get(url, timeout=5).status_code

                        if status_code == 200:
                            first_bank = self.banks[index]
                            found = True
                    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                        with self.lock:
                            self.banks_recconection[self.banks[index]] = True
                        threading.Thread(target=self.loop_reconnection, args=(self.banks[index],)).start()

                index += 1

            else:
                #first_bank = self.ip_bank
                first_bank = self.port
                found = True

        return first_bank

   
    def loop_reconnection(self, ip_bank: str):
        loop = True
        while loop == True:
            try:
                #url = (f"http://{ip_bank}:5070/ready_for_connection")
                url = (f"http://{self.ip_bank}:{ip_bank}/ready_for_connection")
                status_code = requests.get(url, timeout=5).status_code

                if status_code == 200:
                    loop = False
                    with self.lock:
                        self.banks_recconection[ip_bank] = False
                else:
                    raise requests.exceptions.ConnectionError

            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                pass


    def find_account(self, key: str) -> object:
        if key not in self.accounts:
            account = None
        else:
            account = self.accounts[key]

        return account

