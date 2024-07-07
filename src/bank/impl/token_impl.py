""" 
Módulo contendo as funções relacionadas a lógica de manipulação do token.
"""

import time
import requests
import threading
from impl.bank_impl import start_system
from impl.package_impl import add_packages_token, process_packages
from utils.outline_requests import create_result_structure, send_request


def check_first_pass_token(database: object) -> dict:
    """
    Retorna se o token está passando no sistema ou não.

    :param database: Armazenamento do banco.
    :type database: object
    :return: Informação se o token está no sistema ou não.
    :rtype: dict
    """

    response = {"Token está no sistema": database.token.is_passing}
    return response


def check_it_has_token(database: object) -> dict:
    """
    Retorna se o banco possui o token.

    :param database: Armazenamento do banco.
    :type database: object
    :return: Informação se o banco possui o token.
    :rtype: dict
    """

    response = {"Bem sucedido": True, "Possui o token": database.token.it_has}
    return response


def count_time_token(database: object, count_limit: int):
    """
    Loop de contagem do tempo que o banco ficou sem receber o token. Se ultrapassar o tempo 
    limite, são enviadas requisições para todos os bancos verificando se o token está com 
    algum deles. Se estiver, a contagem é resetada, caso não esteja, é chamada a função para 
    casos de detecção de falhas no token. Se nenhum banco estiver disponível para receber 
    mensagens, o banco entra no estado inicial do sistema (função: start_system). 

    :param database: Armazenamento do banco.
    :type database: object
    :param count_limit: Limite de tempo que o banco pode ficar sem receber o token.
    :type count_limit: int
    """

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
                    count_pass = database.token.count_pass
                    database.token.reset_all_atributes()
                    database.token.set_count_pass(count_pass)
                    threading.Thread(target=start_system, args=(database,)).start()

                elif token_in_the_system == False:
                    send_problem_alert(database)

                database.token.set_time(0)

        time.sleep(1)


def multicast_check_it_has(database: object, result_dict: dict, quantity: int):
    """
    Envia para todos os bancos verificando se algum deles possui o token. A estrutura 
    de resultados (result_dict) armazena a indicação da finalização das requisições e 
    os resultados de retorno.

    :param database: Armazenamento do banco.
    :type database: object
    :param result_dict: Estrutura para indicar o término das requisições e os dados retornados.
    :type result_dict: int
    :param quantity: Quantidade de requisições enviadas.
    :type quantity: dict
    """

    for i in range(quantity):
        if database.banks[i] == database.ip_bank:
            result_dict[i]["Terminado"] = True
            result_dict[i]["Resposta"] = {"Bem sucedido": False, "Possui o token": False}

        else:
            if database.banks_recconection[database.banks[i]] == True:
                result_dict[i]["Terminado"] = True
                result_dict[i]["Resposta"] = {"Bem sucedido": False, "Possui o token": None}

            else:
                url = (f"http://{database.banks[i]}:5060/check_it_has_token")
                threading.Thread(target=send_request, args=(database, url, database.banks[i], "", "GET", result_dict, i,)).start()

    loop = True
    while loop == True:
        loop = False
        for key in result_dict.keys():
            if result_dict[key]["Terminado"] == False:
                loop = True


def receive_token(database: object, data_token: dict) -> dict:
    """
    Recebimento do token. Após o recebimento, é chamada, em uma thread, a função de 
    validação do token.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_token: Dados do token recebido.
    :type data_token: dict
    :return: Resultado do recebimento.
    :rtype: dict
    """

    if database.token_problem_alert == False:
        if database.token.is_passing == False:
            database.token.set_is_passing(True)
        threading.Thread(target=check_token_validity, args=(database, data_token,)).start()

    response = {"Bem sucedido": True}
    return response


def check_token_validity(database: object, data_token: dict):
    """
    Checa validade do token. É verificado se o valor de passagem do token atual 
    é igual ao que está armazenado no token, se não for, é chamada a função para 
    casos de detecção de falha no token (função: send_problem_alert). Caso o valor 
    de passagem seja igual, é verificado se o banco atual deve executar os pacotes
    armazenados no token através da estrutura contadora de execução do token. Se ele 
    for o responsável pela execução, ele executa os pacotes armazenados no token (função: 
    process_packages), se não, somente insere seus pacotes no token e o passa adianta. 
    As flags relacionadas ao token são setadas nesses processos.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_token: Dados do token.
    :type data_token: dict
    """

    if database.token.count_pass != data_token["Contadora de passagem do token"][database.ip_bank]:
        if database.token_problem_alert == False:
            send_problem_alert(database)
    
    else:

        database.token.set_it_has(True)
        database.token.set_time(0)

        if data_token["Contadora de execução de pacote"][database.ip_bank] == 1:
            process_packages(database, data_token) 
            database.token.clear_token_execution_counter(data_token["Contadora de execução de pacote"])
        
        if data_token["Contadora de passagem do token"][database.ip_bank] > 100:
            data_token["Contadora de passagem do token"][database.ip_bank] = 0
            database.token.set_count_pass(0)
        else:
            data_token["Contadora de passagem do token"][database.ip_bank] += 1
            database.token.set_count_pass(database.token.count_pass + 1)

        data_token["Contadora de execução de pacote"][database.ip_bank] += 1
        add_packages_token(database, data_token)
        token_pass(database, data_token) 


def token_pass(database: object, data_token: dict):
    """
    Função de passagem do token. É passado o token para o próximo banco que estiver 
    online. Se nenhum estiver online, o banco volta ao estado inicial (função: start_system).

    :param database: Armazenamento do banco.
    :type database: object
    :param data_token: Dados do token.
    :type data_token: dict
    """

    loop = True
    while loop == True:
        if database.token_problem_alert == False:
            next_bank = database.find_next_bank()
            
            try:
                if next_bank != database.ip_bank:
                        url = (f"http://{next_bank}:5060/token_pass")
                        status_code = requests.post(url, json=data_token, timeout=5).status_code

                        if status_code == 200:
                            database.token.set_it_has(False)
                            database.token.set_time(0)

                else:
                    count_pass = database.token.count_pass
                    database.token.reset_all_atributes()
                    database.token.set_count_pass(count_pass)
                    start_system(database)
                
                loop = False

            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                with database.lock:
                    database.banks_recconection[next_bank] = True
                threading.Thread(target=database.loop_reconnection, args=(next_bank,)).start()
        
        else:
            loop = False


def send_problem_alert(database: object):
    """
    Envia para o banco que tem maior prioridade o alerta de detecção de falha no token. 
    Depois o banco seta as flags de indicação de falha e entra no estado de bloqueio 
    temporário (função: reset_problem_alert). Se ele for o banco de maior 
    prioridade, ele mesmo trata a falha no sistema (função: treat_problem).

    :param database: Armazenamento do banco.
    :type database: object
    """

    loop = True
    while loop == True:
        first_bank = database.find_first_bank()

        if first_bank == database.ip_bank:
            threading.Thread(target=treat_problem, args=(database, "",)).start()
            loop = False

        else:
            try:
                data = {"Lidar com o problema": True, "Emissor do alerta": database.ip_bank}
                url = (f"http://{first_bank}:5060/alert_problem_detected")
                response = requests.post(url, json=data, timeout=5).json()

                if response["Bem sucedido"] == True:
                    database.set_token_problem_alert(True)
                    database.token.reset_all_atributes()
                    threading.Thread(target=reset_problem_alert, args=(database,)).start()

                loop = False
            
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                with database.lock:
                    database.banks_recconection[first_bank] = True
                threading.Thread(target=database.loop_reconnection, args=(first_bank,)).start()


def receive_problem_alert(database: object, data_alert: dict) -> dict:
    """
    Recebimento de aviso de problema no sistema do token. É verificado se o aviso é 
    para o banco atual lidar com o problema ou o aviso já é de alguém que está lidando. 
    Se for para ele lidar, ele começa o processo (função: treat_problem), se não, ele 
    seta as flags de indicação de falha e entra em estado de bloqueio (função: 
    reset_problem_alert) para esperar regularizar o sistema.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_alert: Dados relacionados ao alerta de problema.
    :type data_alert: dict
    :return: Resposta ao aviso.
    :rtype: dict
    """

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
        threading.Thread(target=reset_problem_alert, args=(database,)).start()

        response = {"Bem sucedido": True}
        return response
    

def treat_problem(database: object, alert_sender: str):
    """
    Trata de falha no sistema do token. Primeiramente, seta as flags de indicação 
    de falha no sistema. Depois, envia para todos os bancos um alerta de 
    problema no sistema. Depois de todos receberem o aviso, o banco atual espera 
    um intervalo de tempo em estado de bloqueio (função: reset_problem_alert) para 
    esperar a regularização do sistema.

    :param database: Armazenamento do banco.
    :type database: object
    :param alert_sender: Banco a ser ignorado no envio do alerta.
    :type alert_sender: str
    """

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
        elif database.banks[i] != database.ip_bank and database.banks[i] != alert_sender:
            url = (f"http://{database.banks[i]}:5060/alert_problem_detected")
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

    reset_problem_alert(database)


def reset_problem_alert(database: object):
    """
    Espera um intervalo de tempo em estado de bloqueio para esperar o sistema se 
    regularizar de uma falha, depois ele volta ao estado inicial (função: start_system).

    :param database: Armazenamento do banco.
    :type database: object
    """

    time.sleep(5)
    database.set_token_problem_alert(False)
    start_system(database)