import requests
import time
import threading


def add_consortium(database: object, list_ip_banks: list):
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
    start_system(database)


def ready_for_connection(database: object):
    response = {"Bem sucedido": database.ready_for_connection}
    return response


def start_system(database: object):
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
                '''
                # id = database.token.create_token(database.ip_bank)
                id = database.token.create_token(database.port)
                token_pass_counter = database.token.create_token_pass_counter(database.banks)
                database.token.set_id(id)

                data_token = {"ID token": id, "Contadora de passagem do token": token_pass_counter, "Pacotes": []}
                add_packages_token(database, data_token)
                '''

                # data_token = database.token.create_token(database.ip_bank, database.banks)
                data_token = database.token.create_token(database.port, database.banks)
                database.token.set_id(data_token["ID token"])
                add_packages_token(database, data_token)

                #data_token["Contadora de passagem do token"][database.ip_bank] += 1
                data_token["Contadora de passagem do token"][database.port] += 1
                print(data_token)

                # url = (f"http://{database.find_next_bank()}:5070/token_pass")
                url = (f"http://{database.ip_bank}:{database.find_next_bank()}/token_pass")
                response = requests.post(url, json=data_token).json()
                print("ENVIEI O PRIMEIROOOOOOOOOOOOOOOOOOO")

            if database.token_duplicate_alert == True:
                database.set_token_duplicate_alert(False)

            database.token.set_is_passing(True)

        time.sleep(2)


def teste(database: object):
    database.ready_for_connection = True
    '''
    id = database.token.create_token(database.port)
    database.token.set_id(id)
    token_pass_counter = database.token.create_token_pass_counter(database.banks)
    data_token = {"ID token": id, "Contadora de passagem do token": token_pass_counter, "Pacotes": []}
    add_packages_token(database, data_token)
    '''
    # data_token = database.token.create_token(database.ip_bank, database.banks)
    data_token = database.token.create_token(database.port, database.banks)
    database.token.set_id(data_token["ID token"])
    add_packages_token(database, data_token)
    #data_token["Contadora de passagem do token"][database.ip_bank] += 1
    data_token["Contadora de passagem do token"][database.port] += 1
    print(data_token)
    # url = (f"http://{database.find_next_bank()}:5070/token_pass")
    url = (f"http://{database.ip_bank}:5060/token_pass")
    response = requests.post(url, json=data_token).json()
    database.token.set_is_passing(True)


def add_packages_token(database: object, data_token: dict):
    for key in database.packages.keys():
        if database.packages[key]["Adicionado ao token"] == False:
            #data_token["Pacotes"].append({"ID": key, "Dados": database.packages[key]["Dados"], "Origem": database.ip_bank})
            data_token["Pacotes"].append({"ID": key, "Dados": database.packages[key]["Dados"], "Origem": database.port})
            database.set_send_package_to_execution(key)

    print("Pacotes: ", database.packages)


def send_request(database: object, url: str, ip_bank: str, data: dict, http_method: str, result: dict):
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


### TESTE
def process_packages(database: object, data_token: dict):
    final_response = {"Bem sucedido": False}

    for i in range(len(data_token["Pacotes"])):
        
        for j in range(len(data_token["Pacotes"][i])):
            pass





    pass


def request_package(database: object, data_package: dict):
    id = database.add_package(data_package)
    print(database.packages[id])

    while database.packages[id]["Terminado"] == False:
        pass

    response = {"Bem sucedido": database[id]["Bem sucedido"]}
    return response



'''
def count_time_token():
    while True:
        time.sleep(1)
        if database.count_banks_on != 0:
            database.token.time += 1
'''


# PARTE DAS TRANSAÇÕES ANTIGAS
def deposit(database: object, data_deposit: dict) -> dict:
    account = database.find_account(data_deposit["Chave"])

    if account == None:
        response = {"Bem sucedido": False, "Justificativa": "Conta não encontrado"}
        return response

    with account.lock:
        response = account.deposit(data_deposit["Valor"])
    return response


def withdraw(database: object, data_withdraw: dict) -> dict:
    account = database.find_account(data_withdraw["Chave"])

    if account == None:
        response = {"Bem sucedido": False, "Justificativa": "Conta não encontrado"}
        return response

    with account.lock:
        response = account.withdraw(data_withdraw["Valor"])
    return response


###########################################################################################
def send_transfer(database: object, data_transfer: dict) -> dict:
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


def receive_transfer(database: object, data_transfer: dict) -> dict:
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


### Teste ###
def show_all(database: object):
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
        database.accounts[key].show_attributes()