"""
Módulo contendo a classe do armazenamento do banco.
"""

import threading
import socket
import requests
from model.token import Token


class Database:
    """ Classe que representa o armazenamento do banco. """

    ip_bank: str
    banks: list
    banks_recconection: dict
    index_actual_bank: int

    accounts: dict
    users: dict
    packages: dict

    ready_for_connection: bool
    token_problem_alert: bool
    processing_package: bool

    count_accounts: int
    count_packages: int

    token: object
    lock: object

    def __init__(self):
        """
        Inicialização dos atributos base de representação do armazenamento de um banco. 
        Incluindo os seguintes atributos:

            - ip bank: IP do banco;
            - banks: Lista dos bancos do consórcio;
            - banks_recconection: Indica quais bancos estão desconectados;
            - index_actual_bank: Posição do IP do banco atual na lista geral;
            - accounts: Armazenamento das contas dos usuários;
            - users: Armazenamento dos usuários;
            - packages: Armazenamento dos pacotes;
            - ready_for_connection: flag indicando se o banco está pronto para conexão;
            - token_problem_alert: Indica se há um problema na passagem do token;
            - processing_package: Indica se um pacote está sendo processado;
            - count_accounts: Quantidade de contas do armazenamento;
            - count_packages: Quantidade de pacotes do armazenamento;
            - token: Dados relacionados a passagem do token;
            - lock: Usando para evitar conflito na mudança de dados;
        """

        self.ip_bank = socket.gethostbyname(socket.gethostname())
        self.banks = [self.ip_bank]
        self.banks_recconection = {self.ip_bank: False}
        self.index_actual_bank = None

        self.accounts = {}
        self.users = {}
        self.packages = {}

        self.ready_for_connection = False
        self.token_problem_alert = False
        self.processing_package = False

        self.count_accounts = 0
        self.count_packages = 0

        self.token = Token()
        self.lock = threading.Lock()


    def set_token_problem_alert(self, token_problem_alert: bool):
        """
        Seta a informação se um problema foi detectado na passagem do token.

        :param token_problem_alert: Indicação se um problema foi detectado na passagem do token.
        :type token_problem_alert: bool
        """

        with self.lock:
            self.token_problem_alert = token_problem_alert

    
    def add_bank(self, ip_bank: str):
        """
        Adiciona banco a lista de armazenamento.

        :param ip_bank: IP do banco a ser adicionado.
        :type ip_bank: str
        """

        with self.lock:
            self.banks.append(ip_bank)
            self.banks_recconection[ip_bank] = False


    def add_account(self, account: object):
        """
        Adiciona conta na estrutura de armazenamento. Adiciona um a quantidade de contas 
        do armazenamento. A chave para a conta é a sua chave PIX.

        :param account: nova conta a ser armazenada.
        :type account: object
        """

        with self.lock:
            self.count_accounts += 1
            self.accounts[account.key] = account


    def calculate_key(self) -> str:
        """
        Cria o ID da conta usando uma string fixa e a quantidade de contas no armazenamento.

        :return: ID criado para a conta.
        :rtype: str
        """

        key = "AC" + str(self.count_accounts)
        return key


    def add_package(self, data_package: dict) -> int:
        """
        Adiciona pacote ao armazenamento. A quantidade de pacotes no armazenamento é usada 
        como chave para o pacote.

        :param data_package: Dados do pacote.
        :type data_package: dict
        :return: ID usado para armazenar o pacote.
        :rtype: int
        """

        id = self.count_packages
        with self.lock:
            self.packages[id] = {"Dados": data_package, "Terminado": False, "Bem sucedido": None, "Adicionado ao token": False}
            self.count_packages += 1

        return id


    def set_send_package_to_execution(self, id: str):
        """
        Seta a informação de que o pacote foi adicionado ao token para ser executado.

        :param id: ID do pacote.
        :type id: str
        """

        with self.lock:
            self.packages[id]["Adicionado ao token"] = True

   
    def count_banks_on(self) -> int:
        """
        Verifica a quantidade de bancos que estão disponíveis para conexão.

        :return: Quantidade de bancos disponíveis para conexão.
        :rtype: int
        """

        count = 0
        for ip in self.banks_recconection.keys():
            if ip != self.ip_bank and self.banks_recconection[ip] == False:
                count += 1

        return count

    
    def sort_ip_banks(self):
        """
        Ordena de forma crescente a lista de IPs dos bancos da lista do armazenamento. 
        Depois chama a função para setar o índice do IP do banco atual nessa lista.
        """

        for i in range(1, len(self.banks)):
            insert_index = i
            current_value = self.banks.pop(i)
            for j in range(i - 1, -1, -1):
                if int(self.banks[j].replace(".","")) > int(current_value.replace(".","")):
                    insert_index = j
            self.banks.insert(insert_index, current_value)

        self.find_index_actual_bank()


    def find_index_actual_bank(self):
        """
        Encontra o índice do IP do banco atual na lista de armazenamento e seta no atributo.
        """

        for i in range(len(self.banks)):
            if self.banks[i] == self.ip_bank:
                self.index_actual_bank = i
                return

   
    def find_next_bank(self) -> str:
        """
        Encontra o IP do próximo banco online que deve receber o token pela ordem na lista de 
        armazenamento. É checado se o banco está disponível para conexão, se não 
        estver, é tentado o próximo.

        :return: IP do próximo banco online.
        :rtype: str
        """

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
                            url = (f"http://{self.banks[index]}:5060/ready_for_connection")
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
                next_bank = self.ip_bank

        return next_bank

   
    def find_first_bank(self) -> str:
        """
        Encontra o IP do primeiro banco online na ordem da lista de armazenamento. 
        É checado se o banco está disponível para conexão, se não estver, 
        é tentado o próximo.

        :return: IP do primeiro banco online.
        :rtype: str
        """

        first_bank = ""
        found = False
        index = 0

        while found == False and index != len(self.banks):

            if index != self.index_actual_bank:
                if self.banks_recconection[self.banks[index]] == False:
                    try:
                        url = (f"http://{self.banks[index]}:5060/ready_for_connection")
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
                first_bank = self.ip_bank
                found = True

        return first_bank

   
    def loop_reconnection(self, ip_bank: str):
        """
        Loop de checagem de conexão com um banco. É enviada a mensagem de checagem 
        de conexão, caso não seja feita conexão, é tentado de novo. Se a conexão 
        tiver êxito, o loop é terminado.

        :param ip_bank: IP do banco para tentar reconexão.
        :type ip_bank: str
        """

        loop = True
        while loop == True:
            try:
                url = (f"http://{ip_bank}:5060/ready_for_connection")
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
        """
        Retorna uma conta pela chave.

        :param key: Chave da conta a ser procurada.
        :type key: dict
        :return: Retorno da procura pela conta.
        :rtype: object
        """


        if key not in self.accounts:
            account = None
        else:
            account = self.accounts[key]

        return account

