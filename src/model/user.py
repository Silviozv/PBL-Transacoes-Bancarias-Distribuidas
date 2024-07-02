class User:
    cpf: str
    name: str
    have_physical_account: bool

    def __init__(self, data_user):
        self.cpf = data_user["CPF"]
        self.name = data_user["Nome"]
        self.have_physical_account = False


    def set_have_physical_account(self, have_physical_account: bool):
        self.have_physical_account = have_physical_account
