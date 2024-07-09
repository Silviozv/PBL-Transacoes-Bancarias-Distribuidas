""" 
Módulo contendo as funções relacionadas à manipulação de pacotes.
"""

import threading
import requests
from utils.outline_requests import create_result_structure, send_request


def add_packages_token(database: object, data_token: dict):
    """
    Adiciona os pacotes armazenados no sistema na fila de pacotes do token, se houver algum 
    a ser adicionado. É setado nos dados referentes ao pacote que ele foi adicionado ao token. 
    Além dos dados das requisições do pacote, também são colocados no armazenamento do token o
    ID do pacote e o banco de origem, que, no caso, é o atual.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_token: Dados armazenados no token.
    :type data_token: dict
    """

    for key in database.packages.keys():
        if database.packages[key]["Adicionado ao token"] == False:
            with database.lock:
                database.packages[key]["Adicionado ao token"] = True
            data_token["Pacotes"].append({"ID": key, "Dados": database.packages[key]["Dados"], "Origem": database.ip_bank})


def process_packages(database: object, data_token: dict):
    """
    Função de processamento de pacotes armazenados no token. Primeiramente, é setada 
    a flag de indicação de processamento de pacotes. Cada um dos pacotes armazenados no 
    token são percorridos. É verificado se o pacote é referente a um saque ou a um depósito, já
    que são tratados de forma diferente do que uma transferência. Se os dados do pacote forem 
    relacionados a uma ou mais transferências, elas são executadas de forma "paralela" através do 
    uso de threads na função send_request. Depois que todas as transferências são feitas, é 
    verificado se o pacote foi bem sucedido, e, em seguida, essa informação é repassada para 
    os bancos relacionados para eles saberem se devem liberar o dinheiro transferido ou não. 
    Ao final, a fila de pacotes do token é limpa e a flag de processamento de pacotes é liberada.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_token: Dados armazenados no token.
    :type data_token: dict
    """

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
    """
    Recebimento da execução de um pacote. É setado se a execução do pacote foi bem sucedida, quais 
    os motivos caso ele não tenha sido e a indicação que ele foi terminado.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_confirm: Dados da confirmação.
    :type data_confirm: dict
    :return: Retorna o resultado do recebimento da confirmação.
    :rtype: dict
    """

    with database.lock:
        database.packages[data_confirm["ID"]]["Bem sucedido"] = data_confirm["Bem sucedido"]
        database.packages[data_confirm["ID"]]["Justificativas"] = data_confirm["Justificativas"]
        database.packages[data_confirm["ID"]]["Terminado"] = True
    
    response = {"Bem sucedido": True}
    return response


def request_package(database: object, data_package: dict):
    """
    Recebimento de requisição de um pacote. O pacote é adicionado ao armazenamento 
    do banco. É iniciado um loop esperando que o pacote tenha sido executado no 
    sistema. Caso não tenha nenhum banco disponível para conexão, o pacote é 
    executado pelo banco atual.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_package: Dados de um pacote.
    :type data_package: dict
    :return: Retorna o resultado da requisição.
    :rtype: dict
    """

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

    response = {}
    response["Bem sucedido"] = database.packages[id]["Bem sucedido"]
    response["Justificativas"] = database.packages[id]["Justificativas"]
    return response


def reset_packages(database: object):
    """
    Verifica os pacotes que foram inseridos no token e ainda não foram executados. 
    Modifica eles indicando que não foram inseridos no token para serem colocados na fila 
    do armazenamento dele novamente.

    :param database: Armazenamento do banco.
    :type database: object
    """

    for key in database.packages.keys():
        if database.packages[key]["Terminado"] == False and database.packages[key]["Adicionado ao token"] == True:
            with database.lock:
                database.packages[key]["Adicionado ao token"] = False