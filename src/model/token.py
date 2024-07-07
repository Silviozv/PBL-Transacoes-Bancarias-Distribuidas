"""
Módulo contendo a classe do token.
"""

import threading
from datetime import datetime


class Token:
    """ Classe que representa o token. """

    is_passing: bool
    it_has: bool
    time: int
    count_pass: int
    lock: object

    def __init__(self):
        """
        Inicialização dos atributos base de representação do token. Incluindo a indicação 
        se ele está passando no sistema, se o banco está com ele, o tempo que o banco ficou 
        sem recebê-lo e a sua contadora de passagem atual.
        """

        self.is_passing = False
        self.it_has = False
        self.time = 0
        self.count_pass = 0
        self.lock = threading.Lock()


    def set_it_has(self, it_has: bool):
        """
        Seta a informação de posse do token.

        :param it_has: Indicação se o banco possui o token.
        :type it_has: bool
        """

        with self.lock:
            self.it_has = it_has


    def set_is_passing(self, is_passing: bool):
        """
        Seta a informação que indica se o token está passando pelo sistema ou não.

        :param is_passing: Indicação se o token está passando pelo sistema ou não.
        :type is_passing: bool
        """

        with self.lock:
            self.is_passing = is_passing


    def set_time(self, time: int):
        """
        Seta o tempo que o banco ficou sem receber o token.

        :param time: Indicação do tempo que o banco ficou sem receber o token.
        :type time: int
        """

        with self.lock:
            self.time = time


    def set_count_pass(self, new_count: int):
        """
        Seta a contadora de passagem do token.

        :param new_count: Novo valor da contadora de passagem.
        :type new_count: int
        """

        with self.lock:
            self.count_pass = new_count


    def reset_all_atributes(self):
        """
        Reseta todos os atributos do objeto.
        """

        with self.lock:
            self.is_passing = False
            self.it_has = False
            self.time = 0
            self.count_pass = 0


    def create_token(self, banks: list) -> dict:
        """
        Criação do token. As informações do token são: a contadora de passagem do token entre os bancos, 
        usada para detectar duplicação do token; a contadora de execução do token, usada para indicar 
        qual banco deve executar os pacotes; e a lista vazia com os pacotes.

        :param banks: Lista dos IPs dos bancos do consórcio.
        :type banks: list
        :return: Estrutura contendo os dados do token.
        :rtype: dict
        """

        token_pass_counter = {}
        token_execution_counter = {}
        for i in range(len(banks)):
            token_pass_counter[banks[i]] = 0
            token_execution_counter[banks[i]] = 0

        data_token = {"Contadora de passagem do token": token_pass_counter, "Contadora de execução de pacote": token_execution_counter, "Pacotes": []}

        return data_token


    def clear_token_execution_counter(self, token_execution_counter: dict):
        """
        Limpa a estrutura contadora de execução do token, usada para indicar qual banco deve executar 
        os pacotes.

        :param token_execution_counter: Estrutura contadora de execução do token.
        :type token_execution_counter: dict
        """

        for key in token_execution_counter.keys():
            token_execution_counter[key] = 0