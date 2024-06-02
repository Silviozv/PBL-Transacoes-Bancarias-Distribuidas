class User:
    cpf: str
    name: str
    have_physical_account: bool

    def __init__(self, data_user):
        self.cpf = data_user["CPF"]
        self.name = data_user["Nome"]
        self.have_physical_account = False

    def show_attributes(self):
        print("CPF: ", self.cpf)
        print("Nome: ", self.name)
        print("Tem conta física: ", self.have_physical_account)