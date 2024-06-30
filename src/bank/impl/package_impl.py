import threading
import requests
from utils.outline_requests import create_result_structure, send_request


def add_packages_token(database: object, data_token: dict):
    for key in database.packages.keys():
        if database.packages[key]["Adicionado ao token"] == False:
            with database.lock:
                database.packages[key]["Adicionado ao token"] = True
            #data_token["Pacotes"].append({"ID": key, "Dados": database.packages[key]["Dados"], "Origem": database.ip_bank})
            data_token["Pacotes"].append({"ID": key, "Dados": database.packages[key]["Dados"], "Origem": database.port})



def process_packages(database: object, data_token: dict):
    # FOI IMPLEMENTADA  A TRANSFERÊNCIA, AGORA É NECESSÁRIO FAZER A LÓGICA DO BANCO CENTRAL  

    for i in range(len(data_token["Pacotes"])):

        quantity = len(data_token["Pacotes"][i]["Dados"]["Bancos remetentes"])
        result_dict = create_result_structure(quantity)

        for j in range(quantity):
            #url = (f"http://{data_token["Pacotes"][i]["Dados"]["Bancos remetentes"][j]}:5060/send_transfer")
            url = (f"http://{database.ip_bank}:{data_token['Pacotes'][i]['Dados']['Bancos remetentes'][j]}/send_transfer")
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
                #url = (f"http://{data_token['Pacotes'][i]['Dados']['Bancos remetentes'][j]}:5060/send_release_transfer")
                url = (f"http://{database.ip_bank}:{data_token['Pacotes'][i]['Dados']['Bancos remetentes'][j]}/send_release_transfer")
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
                # url = (f"http://{data_token['Pacotes'][i]['Origem']}:5060/confirm_package_execution")
                url = (f"http://{database.ip_bank}:{data_token['Pacotes'][i]['Origem']}/confirm_package_execution")
                response = requests.patch(url, json=data, timeout=5)

            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                with database.lock:
                    database.banks_recconection[data_token["Pacotes"][i]["Origem"]] = True
                threading.Thread(target=database.loop_reconnection, args=(data_token["Pacotes"][i]["Origem"],)).start()

    data_token["Pacotes"] = []


def confirm_package_execution(database: object, data_confirm: dict):

    with database.lock:
        database.packages[data_confirm["ID"]]["Bem sucedido"] = data_confirm["Bem sucedido"]
        database.packages[data_confirm["ID"]]["Justificativas"] = data_confirm["Justificativas"]
        database.packages[data_confirm["ID"]]["Terminado"] = True
    
    response = {"Bem sucedido": True}
    return response


def request_package(database: object, data_package: dict):
    id = database.add_package(data_package)

    while database.packages[id]["Terminado"] == False:
        pass

    response = database.packages[id]
    return response


def reset_packages(database: object):
    for key in database.packages.keys():
        if database.packages[key]["Terminado"] == False and database.packages[key]["Adicionado ao token"] == True:
            with database.lock:
                database.packages[key]["Adicionado ao token"] = False