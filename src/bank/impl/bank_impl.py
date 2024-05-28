from model.database import Database

database = Database()

def register_account(account: object):
    account.set_id(calculate_id(account.cpf))

def calculate_id(cpf: str) -> str:

    count_accounts = len(database.get_accounts())
    id = "AC" + str(count_accounts)
    return id
