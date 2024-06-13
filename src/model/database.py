import threading
import socket
import requests
import time

class Database:
    accounts: dict
    users: dict
    ip_bank: str
    lock: object

    def __init__(self):
        ##
        self.list_ports = ["5090", "5070", "5080"]
        self.port = "5090"
        ##
        self.ip_bank = socket.gethostbyname(socket.gethostname())
        self.banks = [self.ip_bank]
        #self.banks_recconection = {self.ip_bank: False}
        self.banks_recconection = {self.port: False}
        self.index_actual_bank = None

        self.accounts = {}
        self.users = {}
        self.packages = {}

        self.ready_for_connection = False
        self.token = False
        self.token_start_pass = False
        self.time_token = 0

        self.lock = threading.Lock()

    # Teste
    def add_bank(self, ip_bank: str):
        with self.lock:
            #self.banks.append(ip_bank)
            #self.banks_recconection[ip_bank] = False
            self.banks.append(self.ip_bank)
            self.banks_recconection[self.list_ports[int(ip_bank)+1]] = False

    # Teste
    def count_banks_on(self):
        count = 0
        #for ip in self.banks_recconection.keys():
        for port in self.list_ports:
            #if ip != self.ip_bank and self.banks_recconection[ip] == False:
            if port != self.port and self.banks_recconection[port] == False:
                count += 1

        return count

    # Teste
    def sort_ip_banks(self):
        for i in range(1, len(self.banks)):
            insert_index = i
            #current_value = self.banks.pop(i)
            current_value = self.list_ports.pop(i)
            for j in range(i - 1, -1, -1):
                #if int(self.banks[j].replace(".","")) > int(current_value.replace(".","")):
                if int(self.list_ports[j]) > int(current_value):
                    insert_index = j
            #self.banks.insert(insert_index, current_value)
            self.list_ports.insert(insert_index, current_value)
        print(self.list_ports)
        self.find_index_actual_bank()

    def find_index_actual_bank(self):
        for i in range(len(self.banks)):
            #if self.banks[i] == self.ip_bank:
            if self.list_ports[i] == self.port:
                self.index_actual_bank = i
                return

    # Teste
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
                    try:
                        #url = (f"http://{self.banks[index]}:5070/ready_for_connection")
                        url = (f"http://{self.banks[index]}:{self.list_ports[index]}/ready_for_connection")
                        status_code = requests.get(url, timeout=2).status_code

                        if status_code == 200:
                            #next_bank = self.banks[index]
                            next_bank = self.list_ports[index]
                            found = True
                    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                        #if self.banks_recconection[self.banks[index]] == False:
                        if self.banks_recconection[self.list_ports[index]] == False:
                            #self.banks_recconection[self.banks[index]] = True
                            self.banks_recconection[self.list_ports[index]] = True
                            #threading.Thread(target=self.loop_reconnection, args=(self.banks[index],)).start()
                            threading.Thread(target=self.loop_reconnection, args=(index,)).start()

                    index += 1

            else:
                found = True
                #next_bank = self.ip_bank
                next_bank = self.port
        print("Proximo banco: ",next_bank)
        return next_bank

    # Teste
    def find_first_bank(self):
        first_bank = ""
        found = False
        index = 0

        while found == False and index != len(self.banks):

            if index != self.index_actual_bank:
                try:
                    # url = (f"http://{self.banks[index]}:5070/ready_for_connection")
                    url = (f"http://{self.banks[index]}:{self.list_ports[index]}/ready_for_connection")
                    status_code = requests.get(url, timeout=2).status_code

                    if status_code == 200:
                        #first_bank = self.banks[index]
                        first_bank = self.list_ports[index]
                        found = True
                except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                    #if self.banks_recconection[self.banks[index]] == False:
                    if self.banks_recconection[self.list_ports[index]] == False:
                        #self.banks_recconection[self.banks[index]] = True
                        self.banks_recconection[self.list_ports[index]] = True
                        #threading.Thread(target=self.loop_reconnection, args=(self.banks[index],)).start()
                        threading.Thread(target=self.loop_reconnection, args=(index,)).start()

                index += 1

            else:
                #first_bank = self.ip_bank
                first_bank = self.port
                found = True
        print("Peimrio banco: ",first_bank)

        return first_bank

    # Teste
    def loop_reconnection(self, ip_bank: str):
        loop = True
        while loop == True:
            try:
                #url = (f"http://{ip_bank}:5070/ready_for_connection")
                url = (f"http://{self.ip_bank}:{self.list_ports[int(ip_bank)]}/ready_for_connection")
                status_code = requests.get(url, timeout=2).status_code

                if status_code == 200:
                    loop = False
                    # self.banks_recconection[ip_bank] = False
                    self.banks_recconection[self.list_ports[int(ip_bank)]] = False
                else:
                    raise requests.exceptions.ConnectionError

            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                time.sleep(2.5)

    # Teste
    def find_account(self, cpf: str, id: str) -> object:
        list_accounts = self.accounts[cpf]

        account = None
        for i in range(len(list_accounts)):
            if list_accounts[i].id == id:
                account = list_accounts[i]

        return account

    # Teste
    def check_connections(self):
        for i in range(len(self.banks)):
            try:
                url = (f"http://{self.banks[i]}:5070/")
                requests.head(url)
            except (requests.exceptions.ConnectionError) as e:
                if self.banks_recconection[self.banks[i]] == False:
                    self.banks_recconection[self.banks[i]] = True
                    threading.Thread( target=self.loop_reconnection, args=(self.banks[i],)).start()


