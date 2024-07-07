"""
Módulo contendo a classe do usuário.
"""

class User:
    """ Classe que representa um usuário. """

    cpf: str
    name: str
    have_physical_account: bool

    def __init__(self, data_user):
        """
        Inicialização dos atributos base de representação do usuário. Incluindo seu CPF, 
        nome e a indicação se ele tem conta física pessoal ou não.
        """

        self.cpf = data_user["CPF"]
        self.name = data_user["Nome"]
        self.have_physical_account = False


    def set_have_physical_account(self, have_physical_account: bool):
        """
        Seta o atributo que indica se o usuário tem conta física pessoal ou não.

        :param have_physical_account: Indicação se o usuário tem conta física pessoal ou não.
        :type have_physical_account: bool
        """

        self.have_physical_account = have_physical_account
