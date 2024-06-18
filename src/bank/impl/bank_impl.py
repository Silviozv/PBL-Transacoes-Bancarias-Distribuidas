import requests
import time
import threading
from model.database import Database
from model.account import Account
from model.user import User

database = Database()


def add_consortium(list_ip_banks: list):
    for i in range(len(list_ip_banks)):
        database.add_bank(list_ip_banks[i])
        try:
            # url = (f"http://{list_ip_banks[i]}:5070/ready_for_connection")
            url = (f"http://{database.ip_bank}:{list_ip_banks[i]}/ready_for_connection")
            status_code = requests.get(url, timeout=2).status_code

            if status_code != 200:
                raise requests.exceptions.ConnectionError

        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            database.banks_recconection[list_ip_banks[i]] = True
            threading.Thread(target=database.loop_reconnection, args=(list_ip_banks[i],)).start()

    database.sort_ip_banks()
    # threading.Thread( target=count_time_token).start()
    teste()


def ready_for_connection():
    response = {"Bem sucedido": database.ready_for_connection}
    return response


def check_first_pass_token():
    response = {"Token está no sistema": database.token.is_passing, "ID token": database.token.current_id}
    return response


def start_system():
    print("REINICIEIIIIIIIIIIIIIIIIIII")
    database.ready_for_connection = True

    while database.token.is_passing == False:
        print(database.banks_recconection)
        while database.count_banks_on() == 0:
            pass

        # if database.find_first_bank() == database.ip_bank:
        if database.find_first_bank() == database.port:
            # url = (f"http://{database.find_next_bank()}:5070/check_first_pass_token")
            url = (f"http://{database.ip_bank}:{database.find_next_bank()}/check_first_pass_token")
            response = requests.get(url).json()

            if response["Token está no sistema"] == False:
                # id = database.token.create_token(database.ip_bank)
                id = database.token.create_token(database.port)
                database.token.set_id(id)
                data = {"ID token": id}
                # url = (f"http://{database.find_next_bank()}:5070/token_pass")
                url = (f"http://{database.ip_bank}:{database.find_next_bank()}/token_pass")
                response = requests.post(url, json=data).json()
                print("ENVIEI O PRIMEIROOOOOOOOOOOOOOOOOOO")

            if database.token_duplicate_alert == True:
                database.set_token_duplicate_alert(False)

            database.token.set_is_passing(True)

        time.sleep(2)


def teste():
    database.ready_for_connection = True
    id = database.token.create_token(database.port)
    database.token.set_id(id)
    data = {"ID token": id}
    # url = (f"http://{database.find_next_bank()}:5070/token_pass")
    url = (f"http://{database.ip_bank}:5070/token_pass")
    response = requests.post(url, json=data).json()
    database.token.set_is_passing(True)


def receive_token(data_token: dict):
    if database.token_duplicate_alert == False:
        if database.token.is_passing == False:
            database.token.set_is_passing(True)
        threading.Thread(target=check_token_validity, args=(data_token["ID token"],)).start()

    response = {"Bem sucedido": True}
    return response


def check_token_validity(token_id: str):
    if database.token.current_id is None:
        print("AAAAAAAAAAAAAAAA")
        database.token.set_id(token_id)
        database.token.set_it_has(True)
        process_packages()

    elif database.token.current_id == token_id:
        print("BBBBBBBBBBBBBBBBBBBBBBB")
        database.token.set_it_has(True)
        process_packages()

    else:
        print("ID DIFERENTEEEEEEEEEEE")
        if database.token_duplicate_alert == False:
            # PROBLEMA: e se dois identificarem o token duplicado?
            send_alert_token_duplicate()


def send_request(url: str, ip_bank: str, data: dict, http_method: str, result: dict):
    if http_method == "POST":
        try:
            response = requests.post(url, json=data)
            result[ip_bank]["Terminado"] = True
            result[ip_bank]["Resposta"] = response
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            with database.lock:
                database.banks_recconection[ip_bank] = True
            threading.Thread(target=database.loop_reconnection, args=(ip_bank,)).start()
            result[ip_bank]["Terminado"] = False


def send_alert_token_duplicate():
    print("DUPLICACAO DETECTADAAAAAAAAAA")
    # if database.find_first_bank() == database.ip_bank:
    if database.find_first_bank() == database.port:
        threading.Thread(target=treat_duplication, args=("",)).start()

    else:
        # data = {"Lidar com a duplicação": True, "Emissor do alerta": database.ip_bank}
        data = {"Lidar com a duplicação": True, "Emissor do alerta": database.port}
        # url = (f"http://{database.find_first_bank()}:5070/alert_token_duplicate")
        url = (f"http://{database.ip_bank}:{database.find_first_bank()}/alert_token_duplicate")
        response = requests.post(url, json=data).json()

        if response["Bem sucedido"] == True:
            print("AVISEIIIIIIIIIIIIIIIIIIIIIIIII")
            database.set_token_duplicate_alert(True)
            database.token.set_it_has(False)
            database.token.set_is_passing(False)
            database.token.set_id(None)
            start_system()


def receive_alert_token_duplicate(data_alert: dict):
    if data_alert["Lidar com a duplicação"] == True:
        if database.token_duplicate_alert == True:
            response = {"Bem sucedido": False, "Alerta já recebido": True}
            return response
        else:
            threading.Thread(target=treat_duplication, args=(data_alert["Emissor do alerta"],)).start()
            response = {"Bem sucedido": True}
            return response

    else:
        while database.processing_package == True:
            pass

        database.set_token_duplicate_alert(True)
        database.token.set_it_has(False)
        database.token.set_is_passing(False)
        database.token.set_id(None)
        threading.Thread(target=start_system).start()

        response = {"Bem sucedido": True}
        return response


### TESTE
def treat_duplication(alert_sender: str):
    print("TO TRATANDOOOOOOOOOO")
    database.set_token_duplicate_alert(True)
    database.token.set_it_has(False)
    database.token.set_is_passing(False)
    database.token.set_id(None)

    with database.lock:
        database.sending_duplicate_token_alert = True

    for i in range(len(database.banks)):
        if database.banks_recconection[database.banks[i]] == False and database.banks[i] != database.port and \
                database.banks[i] != alert_sender:

            try:
                data = {"Lidar com a duplicação": False}
                # url = (f"http://{database.banks[index]}:5070/alert_token_duplicate")
                url = (f"http://{database.ip_bank}:{database.banks[i]}/alert_token_duplicate")
                response = requests.post(url, json=data).json()

            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                with database.lock:
                    database.banks_recconection[database.banks[i]] = True
                threading.Thread(target=database.loop_reconnection, args=(database.banks[i],)).start()

    time.sleep(10)

    for i in range(len(database.banks)):
        if database.banks_recconection[database.banks[i]] == False and database.banks[i] != database.port:

            try:
                # url = (f"http://{database.banks[index]}:5070/release_duplication_alert")
                url = (f"http://{database.ip_bank}:{database.banks[i]}/release_duplication_alert")
                response = requests.post(url).json()

            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                with database.lock:
                    database.banks_recconection[database.banks[i]] = True
                threading.Thread(target=database.loop_reconnection, args=(database.banks[i],)).start()

    with database.lock:
        database.sending_duplicate_token_alert = False

    start_system()


def release_duplication_alert():
    print("LIBEREIIIIIIIIIIIII")
    database.token.set_id(None)
    database.set_token_duplicate_alert(False)

    response = {"Bem sucedido": True}
    return response


def process_packages():
    time.sleep(4)

    if database.token_duplicate_alert == False:

        data = {"ID token": database.token.current_id}
        # url = (f"http://{database.find_next_bank()}:5070/token_pass")
        url = (f"http://{database.ip_bank}:{database.find_next_bank()}/token_pass")
        status_code = requests.post(url, json=data).status_code

        if status_code == 200:
            print("REPASSEI O PRIMEIROOOOOO")
            database.token.set_it_has(False)
            database.token.time = 0


'''
def count_time_token():
    while True:
        time.sleep(1)
        if database.count_banks_on != 0:
            database.token.time += 1
'''


##### Parte feita para a base dos usuários e das contas
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
        url = (
            f"http://{data_transfer['IP banco']}:5070/receive_transfer/{data_transfer['Valor']}/{data_transfer['Chave PIX']}")
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
def show_all():
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
        print("Contas do usuário: ", key)
        for i in range(len(database.accounts[key])):
            print()
            database.accounts[key][i].show_attributes()