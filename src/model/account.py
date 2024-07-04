"""
Módulo contendo a classe da conta.
"""

import threading


class Account:
    """ Classe que representa uma conta. """

    key: str
    type_account: list
    cpfs: list
    balance: float
    lock: object

    def __init__(self, data_account: dict):
        """
        Inicialização dos atributos base de representação da conta. Incluindo a sua chave, 
        indicação do tipo de conta, CPFs dos usuários vinculados, saldo e o saldo bloqueado.
        """

        self.key = data_account["Chave"]  
        self.type_account = data_account["Tipo de conta"] 
        self.cpfs = data_account["CPFs"]  

        self.balance = 0
        self.blocked_balance = 0

        self.lock = threading.Lock()


    def deposit_balance(self, value: str) -> dict:
        """
        Depositar valor no saldo da conta.

        :param value: Valor a ser depositado.
        :type value: str
        :return: Resposta da ação de depósito.
        :rtype: dict
        """

        with self.lock:
            self.balance += float(value)
        response = {"Bem sucedido": True}

        return response


    def withdraw_balance(self, value: str) -> dict:
        """
        Sacar valor do saldo da conta.

        :param value: Valor a ser sacado.
        :type value: str
        :return: Resposta da ação de saque.
        :rtype: dict
        """

        if self.balance >= float(value):
            response = {"Bem sucedido": True}
            with self.lock:
                self.balance -= float(value)
        else:
            response = {"Bem sucedido": False, "Justificativa": "Saldo insuficiente"}
        
        return response
        

    def deposit_blocked_balance(self, value: str) -> dict:
        """
        Depositar valor no saldo bloqueado da conta .

        :param value: Valor a ser depositado.
        :type value: str
        :return: Resposta da ação de depósito.
        :rtype: dict
        """

        with self.lock:
            self.blocked_balance += float(value)
        response = {"Bem sucedido": True}

        return response


    def withdraw_blocked_balance(self, value: str) -> dict:
        """
        Sacar valor do saldo bloqueado da conta.

        :param value: Valor a ser sacado.
        :type value: str
        :return: Resposta da ação de saque.
        :rtype: dict
        """

        if self.blocked_balance >= float(value):
            response = {"Bem sucedido": True}
            with self.lock:
                self.blocked_balance -= float(value)
        else:
            response = {"Bem sucedido": False, "Justificativa": "Saldo reserva insuficiente"}
        
        return response
