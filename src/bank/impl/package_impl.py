import threading
import requests
from utils.outline_requests import create_result_structure, send_request


def add_packages_token(database: object, data_token: dict):
    for key in database.packages.keys():
        if database.packages[key]["Adicionado ao token"] == False:
            with database.lock:
                database.packages[key]["Adicionado ao token"] = True
            data_token["Pacotes"].append({"ID": key, "Dados": database.packages[key]["Dados"], "Origem": database.ip_bank})


def process_packages(database: object, data_token: dict):
    with database.lock:
        database.processing_package = True

    for i in range(len(data_token["Pacotes"])):

        quantity_senders = len(data_token["Pacotes"][i]["Dados"]["Chaves remetentes"])
        quantity_receivers = len(data_token["Pacotes"][i]["Dados"]["Chaves destinatários"])

        if quantity_senders != quantity_receivers:

            result_dict = create_result_structure(1)

            if quantity_senders > quantity_receivers:
                url = (f"http://{data_token['Pacotes'][i]['Dados']['Bancos remetentes'][0]}:5060/withdraw")
                data = {"Chave": data_token["Pacotes"][i]["Dados"]["Chaves remetentes"][0], 
                        "Valor": data_token["Pacotes"][i]["Dados"]["Valores"][0]}
                threading.Thread(target=send_request, args=(database, url, data_token["Pacotes"][i]["Dados"]["Bancos remetentes"][0], data, "PATCH", result_dict, 0,)).start()

            else:
                url = (f"http://{data_token['Pacotes'][i]['Dados']['Bancos destinatários'][0]}:5060/deposit")
                data = {"Chave": data_token["Pacotes"][i]["Dados"]["Chaves destinatários"][0], 
                        "Valor": data_token["Pacotes"][i]["Dados"]["Valores"][0]}
                threading.Thread(target=send_request, args=(database, url, data_token["Pacotes"][i]["Dados"]["Bancos destinatários"][0], data, "PATCH", result_dict, 0,)).start()

            while result_dict[0]["Terminado"] == False:
                pass

            successful_package = True
            failure_justifications = {}
            response = result_dict[0]['Resposta'].json()
            if response["Bem sucedido"] == False:
                successful_package = False
                failure_justifications[0] = response["Justificativa"]

        else:

            quantity = quantity_senders
            result_dict = create_result_structure(quantity)

            for j in range(quantity):
                url = (f"http://{data_token['Pacotes'][i]['Dados']['Bancos remetentes'][j]}:5060/send_transfer")
                data = {"Chave remetente": data_token["Pacotes"][i]["Dados"]["Chaves remetentes"][j], 
                        "Banco destinatário": data_token["Pacotes"][i]["Dados"]["Bancos destinatários"][j], 
                        "Chave destinatário": data_token["Pacotes"][i]["Dados"]["Chaves destinatários"][j], 
                        "Valor": data_token["Pacotes"][i]["Dados"]["Valores"][j]}
                threading.Thread(target=send_request, args=(database, url, data_token["Pacotes"][i]["Dados"]["Bancos remetentes"][j], data, "PATCH", result_dict, j,)).start()
        
            loop = True
            while loop == True:
                loop = False
                for key in result_dict.keys():
                    if result_dict[key]["Terminado"] == False:
                        loop = True
            
            successful_package = True
            failure_justifications = {}
            failure_transactions = []
            for key in result_dict.keys():
                response = result_dict[key]['Resposta'].json()
                if response["Bem sucedido"] == False:
                    successful_package = False
                    failure_justifications[key] = response["Justificativa"]
                    failure_transactions.append(key)

            for j in range(quantity):

                if j not in failure_transactions:
                    url = (f"http://{data_token['Pacotes'][i]['Dados']['Bancos remetentes'][j]}:5060/send_release_transfer")
                    data = {"Chave remetente": data_token["Pacotes"][i]["Dados"]["Chaves remetentes"][j], 
                            "Banco destinatário": data_token["Pacotes"][i]["Dados"]["Bancos destinatários"][j], 
                            "Chave destinatário": data_token["Pacotes"][i]["Dados"]["Chaves destinatários"][j], 
                            "Valor": data_token["Pacotes"][i]["Dados"]["Valores"][j],
                            "Execução bem sucedida do pacote": successful_package}
                    threading.Thread(target=send_request, args=(database, url, data_token["Pacotes"][i]["Dados"]["Bancos remetentes"][j], data, "PATCH", result_dict, j,)).start()

        if database.banks_recconection[data_token["Pacotes"][i]["Origem"]] == False:
            try:
                data = {"Bem sucedido": successful_package, 
                        "ID": data_token["Pacotes"][i]["ID"], 
                        "Justificativas": failure_justifications}
                url = (f"http://{data_token['Pacotes'][i]['Origem']}:5060/confirm_package_execution")
                response = requests.patch(url, json=data, timeout=5)

            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                with database.lock:
                    database.banks_recconection[data_token["Pacotes"][i]["Origem"]] = True
                threading.Thread(target=database.loop_reconnection, args=(data_token["Pacotes"][i]["Origem"],)).start()

    data_token["Pacotes"] = []

    with database.lock:
        database.processing_package = False


def confirm_package_execution(database: object, data_confirm: dict):

    with database.lock:
        database.packages[data_confirm["ID"]]["Bem sucedido"] = data_confirm["Bem sucedido"]
        database.packages[data_confirm["ID"]]["Justificativas"] = data_confirm["Justificativas"]
        database.packages[data_confirm["ID"]]["Terminado"] = True
    
    response = {"Bem sucedido": True}
    return response


def request_package(database: object, data_package: dict):
    id = database.add_package(data_package)

    loop = True
    while loop == True:
        if database.packages[id]["Terminado"] == True:
            loop = False
        elif database.count_banks_on() == 0:
            data_token = {}
            data_token["Pacotes"] = [{"ID": id, "Dados": database.packages[id]["Dados"], "Origem": database.ip_bank}]
            process_packages(database, data_token)
            loop = False

    response = database.packages[id]
    return response


def reset_packages(database: object):
    for key in database.packages.keys():
        if database.packages[key]["Terminado"] == False and database.packages[key]["Adicionado ao token"] == True:
            with database.lock:
                database.packages[key]["Adicionado ao token"] = False