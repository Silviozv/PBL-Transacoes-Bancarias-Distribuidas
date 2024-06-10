import requests
import time
from model.database import Database
from model.account import Account
from model.user import User

database = Database()


def request_add_bank(ip_bank: str, ips_registered_sender: list):
    if ip_bank in database.banks:
        response = {"Bem sucedido": False, "Justificativa": "O banco já está adicionado"}
        return response

    try:
        url = (f"http://{ip_bank}:5070/")
        requests.head(url)
        database.add_bank(ip_bank)
        response = {"Bem sucedido": True}
    except (requests.exceptions.ConnectionError) as e:
        response = {"Bem sucedido": False, "Justificativa": "Não foi possível conectar ao banco"}
        return response

    for ip in ips_registered_sender:
        if ip not in database.banks:
            try:
                url = (f"http://{ip}:5070/")
                requests.head(url)
                database.add_bank(ip)
            except (requests.exceptions.ConnectionError) as e:
                pass

    list_ips_return = database.banks.copy()
    for ip in ips_registered_sender:
        if ip in list_ips_return:
            list_ips_return.remove(ip)

    response["Novos IPs encontrados"] = list_ips_return
    return response


def check_leader():
    while True:
        try:
            url = (f"http://{database.leader}:5070/verify_leadership")
            status_code = requests.get(url).status_code
            time.sleep(2)

            if status_code == 404:
                raise requests.exceptions.ConnectionError

        except (requests.exceptions.ConnectionError) as e:
            database.check_connections()
            priority_bank = database.find_priority_bank()

            if priority_bank == database.ip_bank:
                # Começar eleição
                pass
            else:
                time.sleep(2.5)


def verify_leadership():
    if (database.leader == database.ip_bank):
        response = {"Liderança": True}
    else:
        response = {"Liderança": False}

    return response


def receive_election_request(ip_candidate: str):
    while database.flag_election == True:
        pass

    if database.leader != "":
        url = (f"/verify_leadership")
        status_code = requests.get(url).status_code

        if status_code == 200:
            response = {"Voto": False, "Líder já eleito": True}
            return response

    with database.lock:
        database.flag_election = True

    if database.leader == ip_candidate:
        response = {"Voto": True}
    elif database.leader != ip_candidate:
        priority_bank = database.find_priority_bank()

        if priority_bank == ip_candidate:
            response = {"Voto": True}
        else:
            response = {"Voto": False, "Líder já eleito": True, "Candidato": priority_bank}






def register_user(data_user: dict) -> dict:
    if data_user["CPF"] in database.users:
        response = {"Bem sucedido": False, "Justificativa": "O usuário já possui uma conta"}
        return response

    user = User(data_user)
    with database.lock:
        database.users[user.cpf] = user
        database.accounts[user.cpf] = []

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
    data_account["Chave"] = str(database.count_accounts)
    database.count_accounts += 1
    account = Account(data_account)
    with database.lock:
        for cpf in data_account["CPFs"]:
            database.accounts[cpf].append(account)

    if data_account["Tipo de conta"][0] == "Fisica" and data_account["Tipo de conta"][1] == "Pessoal":
        with database.lock:
            database.users[account.cpfs[0]].have_physical_account = True

    response = {"Bem sucedido": True}
    return response


def deposit(data_deposit: dict) -> dict:
    if data_deposit["CPF"] not in database.accounts:
        response = {"Bem sucedido": False, "Justificativa": "Usuário não encontrado"}
        return response

    account = database.find_account(data_deposit["CPF"], data_deposit["ID"])

    if account == None:
        response = {"Bem sucedido": False, "Justificativa": "Conta não encontrado"}
        return response

    with account.lock:
        response = account.deposit(data_deposit["Valor"])
    return response


def withdraw(data_withdraw: dict) -> dict:
    if data_withdraw["CPF"] not in database.accounts:
        response = {"Bem sucedido": False, "Justificativa": "Usuário não encontrado"}
        return response

    account = database.find_account(data_withdraw["CPF"], data_withdraw["ID"])

    if account == None:
        response = {"Bem sucedido": False, "Justificativa": "Conta não encontrado"}
        return response

    with account.lock:
        response = account.withdraw(data_withdraw["Valor"])
    return response


###########################################################################################
def send_transfer(data_transfer: dict) -> dict:
    if data_transfer["ID remetente"] not in database.accounts:
        response = {"Bem sucedido": False, "Justificativa": "Conta do remetente não encontrada"}
        return response

    if data_transfer["IP banco"] == database.ip_bank:
        data_search = database.find_account_by_key(data_transfer["Chave PIX"])

        if data_search["Conta encontrada"] == True:

            if database.accounts[data_transfer["ID remetente"]].balance >= float(data_transfer["Valor"]):
                with database.accounts[data_transfer["ID remetente"]].lock:
                    database.accounts[data_transfer["ID remetente"]].withdraw(data_transfer["Valor"])
                with database.accounts[data_search["ID conta"]].lock:
                    database.accounts[data_search["ID conta"]].deposit(data_transfer["Valor"])
                response = {"Bem sucedido": True}
                return response
            else:
                response = {"Bem sucedido": False, "Justificativa": "Saldo insuficiente"}
                return response

        else:
            response = {"Bem sucedido": False, "Justificativa": "Chave não encontrada"}
            return response

    with database.accounts[data_transfer["ID remetente"]].lock:
        response = database.accounts[data_transfer["ID remetente"]].withdraw(data_transfer["Valor"])

    if response["Bem sucedido"] == True:
        url = (f"http://{data_transfer['IP banco']}:5070/receive_transfer/{data_transfer['Valor']}/{data_transfer['Chave PIX']}")
        response = requests.patch(url)

        if response.status_code == 200:
            return response.json()
        else:
            with database.accounts[data_transfer["ID remetente"]].lock:
                database.accounts[data_transfer["ID remetente"]].deposit(data_transfer["Valor"])
            return response.json()

    else:
        return response


def receive_transfer(data_transfer: dict) -> dict:
    data_search = database.find_account_by_key(data_transfer["Chave PIX"])

    if data_search["Conta encontrada"] == True:
        with database.accounts[data_search["ID conta"]].lock:
            database.accounts[data_search["ID conta"]].deposit(data_transfer["Valor"])
        response = {"Bem sucedido": True}
        return response

    else:
        response = {"Bem sucedido": False, "Justificativa": "Chave não encontrada"}
        return response
############################################################################################

def calculate_id() -> str:
    id = "AC" + str(database.count_accounts)
    return id


### Teste ###
def show_all() -> dict:
    print("\n--- BANCOS ---")
    print()
    for i in range(len(database.banks)):
        print(database.banks[i])
    print()

    print("--- USUÁRIOS ---")
    for key in database.users.keys():
        print()
        database.users[key].show_attributes()

    print("\n--- CONTAS ---")
    for key in database.accounts.keys():
        print()
        print("Contas do usuário: ", key )
        for i in range(len(database.accounts[key])):
            print()
            database.accounts[key][i].show_attributes()