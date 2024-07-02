import time
import requests
import threading
from impl.bank_impl import start_system
from impl.package_impl import add_packages_token, process_packages
from utils.outline_requests import create_result_structure, send_request


def check_first_pass_token(database: object):
    response = {"Token está no sistema": database.token.is_passing, "ID token": database.token.current_id}
    return response


def check_it_has_token(database: object):
    response = {"Bem sucedido": True, "Possui o token": database.token.it_has}
    return response


def count_time_token(database: object, count_limit: int):
    database.token.set_time(0)
    quantity = int(count_limit/10)
    while True:
        if database.token.is_passing == True and database.processing_package == False:
            database.token.set_time(database.token.time + 1)

            if database.token.time > count_limit:
                result_dict = create_result_structure(quantity)
                multicast_check_it_has(database, result_dict, quantity)

                quantity_disconnected = 0
                token_in_the_system = False
                for key in result_dict.keys():
                    if isinstance(result_dict[key]["Resposta"], dict) == False:
                        result_dict[key]["Resposta"] = result_dict[key]["Resposta"].json()
                    if result_dict[key]["Resposta"]["Bem sucedido"] == True:
                        if result_dict[key]["Resposta"]["Possui o token"] == True:
                            token_in_the_system = True
                    else:
                        quantity_disconnected += 1

                if quantity_disconnected == quantity:

                    database.token.reset_all_atributes()
                    threading.Thread(target=start_system, args=(database,)).start()

                elif token_in_the_system == False:
                    send_problem_alert(database)

                database.token.set_time(0)

        time.sleep(1)


def multicast_check_it_has(database: object, result_dict: dict, quantity: int):
    for i in range(quantity):
        #if database.banks[i] == database.ip_bank:
        if database.banks[i] == database.port:
            result_dict[i]["Terminado"] = True
            result_dict[i]["Resposta"] = {"Bem sucedido": False, "Possui o token": False}

        else:
            if database.banks_recconection[database.banks[i]] == True:
                result_dict[i]["Terminado"] = True
                result_dict[i]["Resposta"] = {"Bem sucedido": False, "Possui o token": None}

            else:
                #url = (f"http://{database.banks[i]}:5060/check_it_has_token")
                url = (f"http://{database.ip_bank}:{database.banks[i]}/check_it_has_token")
                threading.Thread(target=send_request, args=(database, url, database.banks[i], "", "GET", result_dict, i,)).start()

    loop = True
    while loop == True:
        loop = False
        for key in result_dict.keys():
            if result_dict[key]["Terminado"] == False:
                loop = True


def receive_token(database: object, data_token: dict):
    if database.token_problem_alert == False:
        if database.token.is_passing == False:
            database.token.set_is_passing(True)
        threading.Thread(target=check_token_validity, args=(database, data_token,)).start()

    response = {"Bem sucedido": True}
    return response


def check_token_validity(database: object, data_token: dict):
    if database.token.current_id != None and database.token.current_id != data_token["ID token"]:
        if database.token_problem_alert == False:
            # PROBLEMA: e se dois identificarem o token duplicado?
            send_problem_alert(database)
    
    else:
        if database.token.current_id is None:
            database.token.set_id(data_token["ID token"])

        database.token.set_it_has(True)
        database.token.set_time(0)

        #if data_token["Contadora de passagem do token"][database.ip_bank] == 1:
        if data_token["Contadora de passagem do token"][database.port] == 1:
            process_packages(database, data_token) 
            database.token.clear_token_pass_counter(data_token["Contadora de passagem do token"])
        
        #data_token["Contadora de passagem do token"][database.ip_bank] += 1
        data_token["Contadora de passagem do token"][database.port] += 1
        add_packages_token(database, data_token)
        token_pass(database, data_token) 


def token_pass(database: object, data_token: dict):
    loop = True
    while loop == True:
        if database.token_problem_alert == False:
            next_bank = database.find_next_bank()
            try:
                #if next_bank != database.ip_bank:
                if next_bank != database.port:

                        # url = (f"http://{next_bank()}:5060/token_pass")
                        url = (f"http://{database.ip_bank}:{next_bank}/token_pass")
                        status_code = requests.post(url, json=data_token, timeout=5).status_code

                        if status_code == 200:
                            database.token.set_it_has(False)
                            database.token.set_time(0)

                else:
                    database.token.reset_all_atributes()
                    start_system(database)
                
                loop = False

            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                with database.lock:
                    database.banks_recconection[next_bank] = True
                threading.Thread(target=database.loop_reconnection, args=(next_bank,)).start()
        
        else:
            loop = False


def send_problem_alert(database: object):
    # if database.find_first_bank() == database.ip_bank:
    if database.find_first_bank() == database.port:
        threading.Thread(target=treat_problem, args=(database, "",)).start()

    else:
        # data = {"Lidar com o problema": True, "Emissor do alerta": database.ip_bank}
        data = {"Lidar com o problema": True, "Emissor do alerta": database.port}
        # url = (f"http://{database.find_first_bank()}:5060/alert_problem_detected")
        url = (f"http://{database.ip_bank}:{database.find_first_bank()}/alert_problem_detected")
        response = requests.post(url, json=data).json()

        if response["Bem sucedido"] == True:
            database.set_token_problem_alert(True)
            database.token.reset_all_atributes()
            threading.Thread(target=reset_duplication_alert, args=(database,)).start()


def receive_problem_alert(database: object, data_alert: dict):
    if data_alert["Lidar com o problema"] == True:
        if database.token_problem_alert == True:
            response = {"Bem sucedido": False, "Alerta já recebido": True}
            return response
        else:
            threading.Thread(target=treat_problem, args=(database, data_alert["Emissor do alerta"],)).start()
            response = {"Bem sucedido": True}
            return response

    else:
        while database.processing_package == True:
            pass

        database.set_token_problem_alert(True)
        database.token.reset_all_atributes()
        threading.Thread(target=reset_duplication_alert, args=(database,)).start()

        response = {"Bem sucedido": True}
        return response
    

def treat_problem(database: object, alert_sender: str):
    database.set_token_problem_alert(True)
    database.token.reset_all_atributes()

    if alert_sender != "":
        quantity = len(database.banks) - 2
    else:
        quantity = len(database.banks) - 1
    result_dict = create_result_structure(quantity)

    j = 0
    for i in range(len(database.banks)):
        if database.banks_recconection[database.banks[i]] == True:
            result_dict[j]["Terminado"] = True
            j += 1
        elif database.banks[i] != database.port and database.banks[i] != alert_sender:
            # url = (f"http://{database.banks[index]}:5060/alert_problem_detected")
            url = (f"http://{database.ip_bank}:{database.banks[i]}/alert_problem_detected")
            data = {"Lidar com o problema": False}
            threading.Thread(target=send_request, args=(database, url, database.banks[i], data, "POST", result_dict, j,)).start()
            j += 1

    if quantity != 0:
        loop = True
        while loop == True:
            loop = False
            for key in result_dict.keys():
                if result_dict[key]["Terminado"] == False:
                    loop = True

    time.sleep(7)

    database.set_token_problem_alert(False)

    start_system(database)


def reset_duplication_alert(database: object):
    time.sleep(5)
    database.set_token_problem_alert(False)
    start_system(database)