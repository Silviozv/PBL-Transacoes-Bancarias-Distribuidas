from model.database import Database
from model.account import Account
from model.user import User

database = Database()


def register_user(data_user: dict) -> dict:
    if data_user["CPF"] in database.users:
        response = {"Bem sucedido": False, "Justificativa": "O usuário já possui uma conta"}
        return response

    user = User(data_user)
    with database.lock:
        database.users[user.cpf] = user

    response = {"Bem sucedido": True}
    return response


def register_account(data_account: dict) -> dict:
    if data_account["Tipo de conta"][0] == "Fisica" and data_account["Tipo de conta"][1] == "Pessoal":
            if data_account["CPFs"][0] in database.users:
                if database.users[data_account["CPFs"][0]].have_physical_account == True:
                    response = {"Bem sucedido": False, "Justificativa": "O usuário já possui uma conta física"}
                    return response

    for cpf in data_account["CPFs"]:
        if cpf not in database.users:
            response = {"Bem sucedido": False, "Justificativa": "Usuário não encontrado"}
            return response

    id = calculate_id()
    data_account["ID"] = id
    data_account["Chave"] = len(database.accounts)
    account = Account(data_account)
    with database.lock:
        database.accounts[id] = account

    if data_account["Tipo de conta"][0] == "Fisica" and data_account["Tipo de conta"][1] == "Pessoal":
        with database.lock:
            database.users[account.cpfs[0]].have_physical_account = True

    response = {"Bem sucedido": True}
    return response


def deposit(id: str, value: str) -> dict:
    if id not in database.accounts:
        response = {"Bem sucedido": False, "Justificativa": "Conta não encontrada"}
        return response

    with database.accounts[id].lock:
        response = database.accounts[id].deposit(value)
    return response


def withdraw(id: str, value: str) -> dict:
    if id not in database.accounts:
        response = {"Bem sucedido": False, "Justificativa": "Conta não encontrada"}
        return response

    with database.accounts[id].lock:
        response = database.accounts[id].withdraw(value)
    return response


def calculate_id() -> str:
    id = "AC" + str(len(database.accounts))
    return id


### Teste ###
def show_all() -> dict:
    print("--- USUÁRIOS ---")
    for key in database.users.keys():
        print()
        database.users[key].show_attributes()

    print("\n--- CONTAS ---")
    for key in database.accounts.keys():
        print()
        database.accounts[key].show_attributes()