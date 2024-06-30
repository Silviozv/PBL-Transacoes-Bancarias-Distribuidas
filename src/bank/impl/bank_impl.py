import requests
import time
import threading
from utils.outline_requests import create_result_structure, send_request
from impl.package_impl import add_packages_token, reset_packages


def add_consortium(database: object, list_ip_banks: list):
    #if database.ip_bank in list_ip_banks:
    if database.port in list_ip_banks:
        #list_ip_banks.remove(database.ip_bank)
        list_ip_banks.remove(database.port)

    result_dict = create_result_structure(len(list_ip_banks))

    for i in range(len(list_ip_banks)):
        database.add_bank(list_ip_banks[i])
        #url = (f"http://{list_ip_banks[i]}:5060/ready_for_connection")
        url = (f"http://{database.ip_bank}:{list_ip_banks[i]}/ready_for_connection")
        threading.Thread(target=send_request, args=(database, url, list_ip_banks[i], "", "GET", result_dict, i,)).start()

    loop = True
    while loop == True:
        loop = False
        for key in result_dict.keys():
            if result_dict[key]["Terminado"] == False:
                loop = True

    database.sort_ip_banks()
    database.token.reset_all_atributes()
    start_system(database)


def ready_for_connection(database: object):
    response = {"Bem sucedido": database.ready_for_connection}
    return response


def start_system(database: object):
    database.ready_for_connection = True
    reset_packages(database)

    while database.token.is_passing == False:
        while database.count_banks_on() == 0:
            pass

        # if database.find_first_bank() == database.ip_bank:
        if database.find_first_bank() == database.port:
            # url = (f"http://{database.find_next_bank()}:5070/check_first_pass_token")
            url = (f"http://{database.ip_bank}:{database.find_next_bank()}/check_first_pass_token")
            response = requests.get(url).json()

            if response["Token está no sistema"] == False:

                # data_token = database.token.create_token(database.ip_bank, database.banks)
                data_token = database.token.create_token(database.port, database.banks)
                database.token.set_id(data_token["ID token"])
                add_packages_token(database, data_token)

                #data_token["Contadora de passagem do token"][database.ip_bank] += 1
                data_token["Contadora de passagem do token"][database.port] += 1

                # url = (f"http://{database.find_next_bank()}:5070/token_pass")
                url = (f"http://{database.ip_bank}:{database.find_next_bank()}/token_pass")
                response = requests.post(url, json=data_token).json()

            database.token.set_is_passing(True)

        time.sleep(2)


def teste(database: object):
    database.ready_for_connection = True
    # data_token = database.token.create_token(database.ip_bank, database.banks)
    data_token = database.token.create_token(database.port, database.banks)
    database.token.set_id(data_token["ID token"])
    add_packages_token(database, data_token)
    #data_token["Contadora de passagem do token"][database.ip_bank] += 1
    data_token["Contadora de passagem do token"][database.port] += 1
    # url = (f"http://{database.find_next_bank()}:5070/token_pass")
    url = (f"http://{database.ip_bank}:5070/token_pass")
    response = requests.post(url, json=data_token).json()
    database.token.set_is_passing(True)
    

# PARTE DAS TRANSAÇÕES ANTIGAS
def deposit(database: object, data_deposit: dict) -> dict:
    account = database.find_account(data_deposit["Chave"])

    if account == None:
        response = {"Bem sucedido": False, "Justificativa": "Conta não encontrado"}
        return response

    response = account.deposit_balance(data_deposit["Valor"])
    return response


def withdraw(database: object, data_withdraw: dict) -> dict:
    account = database.find_account(data_withdraw["Chave"])

    if account == None:
        response = {"Bem sucedido": False, "Justificativa": "Conta não encontrado"}
        return response

    response = account.withdraw_balance(data_withdraw["Valor"])
    return response


# FALTA FAZER O SALDO BLOQUEADO CASO O PACOTE TENHA ALGUM ERRO
def send_transfer(database: object, data_transfer: dict) -> dict:
    if data_transfer["Chave remetente"] not in database.accounts:
        response = {"Bem sucedido": False, "Justificativa": "Conta do remetente não encontrada"}

    else:
        if database.accounts[data_transfer["Chave remetente"]].balance < float(data_transfer["Valor"]):
            response = {"Bem sucedido": False, "Justificativa": "Saldo insuficiente"}

        else:
            #if data_transfer["Banco destinatário"] == database.ip_bank:
            if data_transfer["Banco destinatário"] == database.port:

                if data_transfer["Chave destinatário"] not in database.accounts:
                    response = {"Bem sucedido": False, "Justificativa": "Conta do destinatário não encontrada"}
                else:
                    database.accounts[data_transfer["Chave remetente"]].withdraw_balance(data_transfer["Valor"])
                    database.accounts[data_transfer["Chave destinatário"]].deposit_blocked_balance(data_transfer["Valor"])
                    response = {"Bem sucedido": True}
                
            else:
                if database.banks_recconection[data_transfer['Banco destinatário']] == True:
                    response = {"Bem sucedido": False, "Justificativa": "Banco desconectado"}

                else:
                    try:
                        data_receive = {"Chave destinatário": data_transfer["Chave destinatário"], "Valor": data_transfer["Valor"]}
                        # url = (f"http://{data_transfer['Banco destinatário']}:5060/receive_transfer")
                        url = (f"http://{database.ip_bank}:{data_transfer['Banco destinatário']}/receive_transfer")
                        response = requests.patch(url, json=data_receive, timeout=5)

                        if response.status_code == 200:
                            database.accounts[data_transfer["Chave remetente"]].withdraw_balance(data_transfer["Valor"])
                        
                        response = response.json()

                    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                        with database.lock:
                            database.banks_recconection[data_transfer['Banco destinatário']] = True
                        threading.Thread(target=database.loop_reconnection, args=(data_transfer['Banco destinatário'],)).start()
                        response = {"Bem sucedido": False, "Justificativa": "Banco desconectado"}
              
    return response


def receive_transfer(database: object, data_transfer: dict) -> dict:
    if data_transfer["Chave destinatário"] not in database.accounts:
        response = {"Bem sucedido": False, "Justificativa": "Conta do destinatário não encontrada"}
    
    else:
        database.accounts[data_transfer["Chave destinatário"]].deposit_blocked_balance(data_transfer["Valor"])
        response = {"Bem sucedido": True}
    
    return response


def send_release_transfer(database: object, data_transfer: dict) -> dict:
 
    #if data_transfer["Banco destinatário"] == database.ip_bank:
    if data_transfer["Banco destinatário"] == database.port:
        
        if data_transfer["Execução bem sucedida do pacote"] == True:
            database.accounts[data_transfer["Chave destinatário"]].withdraw_blocked_balance(data_transfer["Valor"])
            database.accounts[data_transfer["Chave destinatário"]].deposit_balance(data_transfer["Valor"])
        
        else:
            database.accounts[data_transfer["Chave destinatário"]].withdraw_blocked_balance(data_transfer["Valor"])
            database.accounts[data_transfer["Chave remetente"]].deposit_balance(data_transfer["Valor"])

        response = {"Bem sucedido": True}

    else:
        if database.banks_recconection[data_transfer['Banco destinatário']] == True:
            response = {"Bem sucedido": False, "Justificativa": "Banco desconectado"}

        else:
            try:
                data_receive = {"Chave destinatário": data_transfer["Chave destinatário"], "Valor": data_transfer["Valor"], "Execução bem sucedida do pacote": data_transfer["Execução bem sucedida do pacote"]}
                # url = (f"http://{data_transfer['Banco destinatário']}:5060/receive_release_transfer")
                url = (f"http://{database.ip_bank}:{data_transfer['Banco destinatário']}/receive_release_transfer")
                response = requests.patch(url, json=data_receive, timeout=5)

                if response.status_code != 200 or data_transfer["Execução bem sucedida do pacote"] == False:
                    database.accounts[data_transfer["Chave remetente"]].deposit_balance(data_transfer["Valor"])
                
                response = response.json()

            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                with database.lock:
                    database.banks_recconection[data_transfer['Banco destinatário']] = True
                threading.Thread(target=database.loop_reconnection, args=(data_transfer['Banco destinatário'],)).start()
                response = {"Bem sucedido": False, "Justificativa": "Banco desconectado"}
            
    return response


def receive_release_transfer(database: object, data_transfer: dict) -> dict:
    if data_transfer["Chave destinatário"] not in database.accounts:
        response = {"Bem sucedido": False, "Justificativa": "Conta do destinatário não encontrada"}
    
    else:
        database.accounts[data_transfer["Chave destinatário"]].withdraw_blocked_balance(data_transfer["Valor"])

        if data_transfer["Execução bem sucedida do pacote"] == True:
            database.accounts[data_transfer["Chave destinatário"]].deposit_balance(data_transfer["Valor"])
        
        response = {"Bem sucedido": True}
    
    return response
                

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