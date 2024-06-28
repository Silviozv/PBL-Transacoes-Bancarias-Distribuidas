import time
import requests
import threading
from impl.bank_impl import start_system, add_packages_token, process_packages


def check_first_pass_token(database: object):
    response = {"Token está no sistema": database.token.is_passing, "ID token": database.token.current_id}
    return response


def receive_token(database: object, data_token: dict):
    if database.token_duplicate_alert == False:
        if database.token.is_passing == False:
            database.token.set_is_passing(True)
        threading.Thread(target=check_token_validity, args=(database, data_token,)).start()

    print(data_token)
    response = {"Bem sucedido": True}
    return response


def check_token_validity(database: object, data_token: dict):
    if database.token.current_id != None and database.token.current_id != data_token["ID token"]:
        print("ID DIFERENTEEEEEEEEEEE")
        if database.token_duplicate_alert == False:
            # PROBLEMA: e se dois identificarem o token duplicado?
            send_alert_token_duplicate(database)
    
    else:
        if database.token.current_id is None:
            print("AAAAAAAAAAAAAAAA")
            database.token.set_id(data_token["ID token"])

        database.token.set_it_has(True)

        #if data_token["Contadora de passagem do token"][database.ip_bank] == 1:
        if data_token["Contadora de passagem do token"][database.port] == 1:
            print("\nTEM QUE EXECUTAR OS PACOTEEEEEEE\n")
            process_packages(database, data_token) 
            database.token.clear_token_pass_counter(data_token["Contadora de passagem do token"])
        
        #data_token["Contadora de passagem do token"][database.ip_bank] += 1
        data_token["Contadora de passagem do token"][database.port] += 1
        add_packages_token(database, data_token)
        token_pass(database, data_token) 

    
'''
    if database.token.current_id is None:
        print("AAAAAAAAAAAAAAAA")
        database.token.set_id(data_token["ID token"])
        database.token.set_it_has(True)
        token_pass(database, data_token)

    elif database.token.current_id == data_token["ID token"]:
        print("BBBBBBBBBBBBBBBBBBBBBBB")
        database.token.set_it_has(True)
        token_pass(database, data_token)

    else:
        print("ID DIFERENTEEEEEEEEEEE")
        if database.token_duplicate_alert == False:
            # PROBLEMA: e se dois identificarem o token duplicado?
            send_alert_token_duplicate(database)
'''


def token_pass(database: object, data_token: dict):
    time.sleep(4)

    if database.token_duplicate_alert == False:

        # url = (f"http://{database.find_next_bank()}:5070/token_pass")
        url = (f"http://{database.ip_bank}:{database.find_next_bank()}/token_pass")
        status_code = requests.post(url, json=data_token).status_code

        if status_code == 200:
            print("REPASSEI O PRIMEIROOOOOO")
            database.token.set_it_has(False)
            database.token.time = 0


def send_alert_token_duplicate(database: object):
    print("DUPLICACAO DETECTADAAAAAAAAAA")
    # if database.find_first_bank() == database.ip_bank:
    if database.find_first_bank() == database.port:
        threading.Thread(target=treat_duplication, args=(database, "",)).start()

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
            start_system(database)


def receive_alert_token_duplicate(database: object, data_alert: dict):
    if data_alert["Lidar com a duplicação"] == True:
        if database.token_duplicate_alert == True:
            response = {"Bem sucedido": False, "Alerta já recebido": True}
            return response
        else:
            threading.Thread(target=treat_duplication, args=(database, data_alert["Emissor do alerta"],)).start()
            response = {"Bem sucedido": True}
            return response

    else:
        while database.processing_package == True:
            pass

        database.set_token_duplicate_alert(True)
        database.token.set_it_has(False)
        database.token.set_is_passing(False)
        database.token.set_id(None)
        threading.Thread(target=reset_duplication_alert, args=(database,)).start()

        response = {"Bem sucedido": True}
        return response
    

### TESTE
def treat_duplication(database: object, alert_sender: str):
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

    time.sleep(5)

    with database.lock:
        database.sending_duplicate_token_alert = False

    '''
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
    '''

    start_system(database)


def reset_duplication_alert(database: object):
    time.sleep(5)
    database.token.set_id(None)
    database.set_token_duplicate_alert(False)
    start_system(database)