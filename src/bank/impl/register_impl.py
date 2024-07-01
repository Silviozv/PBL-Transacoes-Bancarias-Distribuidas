from model.account import Account
from model.user import User


def register_user(database: object, data_user: dict) -> dict:
    if data_user["CPF"] in database.users:
        response = {"Bem sucedido": False, "Justificativa": "O usuário já possui uma conta"}
        return response

    user = User(data_user)
    with database.lock:
        database.users[user.cpf] = user
    
    response = {"Bem sucedido": True}
    return response


def register_account(database: object, data_account: dict) -> dict:
    if data_account["Tipo de conta"][0] == "Física" and data_account["Tipo de conta"][1] == "Pessoal":
        if data_account["CPFs"][0] in database.users:
            if database.users[data_account["CPFs"][0]].have_physical_account == True:
                response = {"Bem sucedido": False, "Justificativa": "O usuário já possui uma conta física"}
                return response

    for cpf in data_account["CPFs"]:
        if cpf not in database.users:
            response = {"Bem sucedido": False, "Justificativa": "Usuário não encontrado"}
            return response

    key = database.calculate_key()
    data_account["Chave"] = key
    account = Account(data_account)
    database.add_account(account)

    if data_account["Tipo de conta"][0] == "Física" and data_account["Tipo de conta"][1] == "Pessoal":
        with database.lock:
            database.users[account.cpfs[0]].set_have_physical_account(True)

    response = {"Bem sucedido": True}
    return response
