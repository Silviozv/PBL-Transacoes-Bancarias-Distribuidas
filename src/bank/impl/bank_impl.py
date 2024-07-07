""" 
Módulo contendo as funções relacionadas à implementação geral do banco.
"""

import requests
import time
import threading
from utils.outline_requests import create_result_structure, send_request
from impl.package_impl import add_packages_token, reset_packages


def ready_for_connection(database: object) -> dict:
    """
    Retorna se o banco está pronto para conexão.

    :param database: Armazenamento do banco.
    :type database: object
    :return: Informação se o banco está pronto para conexão.
    :rtype: dict
    """

    response = {"Bem sucedido": database.ready_for_connection}
    return response


def check_user(database: object, data_check: dict) -> dict:
    """
    Retorna se o usuário indicado pelo CPF está cadastrado no armazenamento. 
    Se o usuário estiver, é retornado o seu nome.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_check: Dados do usuário para a verificação.
    :type data_check: dict
    :return: Informação se o usuário está cadastrado.
    :rtype: dict
    """

    if data_check["CPF"] in database.users.keys():
        response = {"Usuário encontrado": True, "Nome do usuário": database.users[data_check["CPF"]].name}
    else:
        response = {"Usuário encontrado": False}

    return response


def get_account_consortium(database: object, data_user: dict) -> dict:
    """
    Verifica com todos os bancos do consórcio quais as contas que o 
    usuário indicado possui e os dados de cada uma. As informações 
    são retornadas.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_user: Dados do usuário.
    :type data_user: dict
    :return: Dados das contas do consórcio vinculadas ao usuário.
    :rtype: dict
    """

    accounts = {}
    for i in range(len(database.banks)):
        if database.banks[i] == database.ip_bank:
            response = get_account_by_user(database, data_user)
            if response["Bem sucedido"] == True:
                accounts[database.banks[i]] = response["Contas"]
        else:
            try:
                url = (f"http://{database.banks[i]}:5060/get/account/user")
                response = requests.get(url, json=data_user, timeout=5)

                if response.status_code == 200:
                    response = response.json()
                    accounts[database.banks[i]] = response["Contas"]
            
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                pass

    if len(accounts) == 0:
        response = {"Bem sucedido": False}
    else:
        response = {"Bem sucedido": True, "Contas": accounts}

    return response


def get_account_by_user(database: object, data_user: dict) -> dict:
    """
    Retorna as contas do banco vinculadas ao usuário indicado.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_user: Dados do usuário.
    :type data_user: dict
    :return: Dados das contas do banco vinculadas ao usuário.
    :rtype: dict
    """

    accounts = []
    for key in database.accounts.keys():
        for i in range(len(database.accounts[key].cpfs)):
            if database.accounts[key].cpfs[i] == data_user["CPF usuário"]:
                data_account = {"Chave": database.accounts[key].key, 
                                "Tipo de conta": database.accounts[key].type_account,
                                "CPFs": database.accounts[key].cpfs,
                                "Saldo": database.accounts[key].balance}
                accounts.append(data_account)

    if len(accounts) == 0:
        response = {"Bem sucedido": False}
    else:
        response = {"Bem sucedido": True, "Contas": accounts}

    return response


def check_account_by_id(database: object, data_account: dict) -> dict:
    """
    Checa se existe uma conta armazenada com o ID indicado.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_account: Dados da conta.
    :type data_account: dict
    :return: Informação se a conta existe no armazenamento.
    :rtype: dict
    """

    if data_account["ID conta"] in database.accounts.keys():
        if data_account['CPF usuário'] in database.accounts[data_account["ID conta"]].cpfs:
            response = {"Bem sucedido": True}
        else:
            response = {"Bem sucedido": False}
    else:
        response = {"Bem sucedido": False}

    return response


def add_consortium(database: object, list_ip_banks: list):
    """
    Adiciona os IPs da lista indica na lista de bancos do consórcio no 
    armazenamento. Verifica com cada banco se estão prontos para conexão, 
    se não, é iniciado um loop de reconexão. Quando todos são verificados, 
    é ordenada a lista do menor para o menor IP, depois o sistema vai para 
    o estado inicial para se preparar para a passagem do token (função: start_system).

    :param database: Armazenamento do banco.
    :type database: object
    :param list_ip_banks: Lista de bancos a serem adicionados.
    :type list_ip_banks: list
    """

    if database.ip_bank in list_ip_banks:
        list_ip_banks.remove(database.ip_bank)

    result_dict = create_result_structure(len(list_ip_banks))

    for i in range(len(list_ip_banks)):
        database.add_bank(list_ip_banks[i])
        url = (f"http://{list_ip_banks[i]}:5060/ready_for_connection")
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


def start_system(database: object):
    """
    Estado inicial do sistema do banco. Caso o token não esteja passando, 
    inicia a lógica de iniciar sua passagem. Entra em um loop que só é interrompido 
    se mais de um banco estiver online além do atual. É verificado se primeiro banco 
    na lista de prioridade é o atual, se for, ele verifica se o token já está passando 
    com o próximo banco na ordem, se não estiver, ele cria o token e o passa adiante. Se 
    o banco atual não for o de maior prioridade, o loop continua até que o token comece a passar.

    :param database: Armazenamento do banco.
    :type database: object
    """

    database.ready_for_connection = True
    reset_packages(database)

    while database.token.is_passing == False:
        while database.count_banks_on() == 0:
            pass

        if database.find_first_bank() == database.ip_bank:
            next_bank = database.find_next_bank()

            try:
                url = (f"http://{next_bank}:5060/check_first_pass_token")
                response = requests.get(url, timeout=5).json()

                if response["Token está no sistema"] == False:

                    data_token = database.token.create_token(database.banks)
                    add_packages_token(database, data_token)

                    data_token["Contadora de execução de pacote"][database.ip_bank] += 1

                    url = (f"http://{next_bank}:5060/token_pass")
                    response = requests.post(url, json=data_token, timeout=5).json()

                database.token.set_is_passing(True)

            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                with database.lock:
                    database.banks_recconection[next_bank] = True
                threading.Thread(target=database.loop_reconnection, args=(next_bank,)).start()

        time.sleep(2)


def deposit(database: object, data_deposit: dict) -> dict:
    """
    Deposita um valor no saldo de uma conta indicada do armazenamento, se ela for encontrada. 
    O resultado da operação é retornado.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_deposit: Dados do depósito.
    :type data_deposit: dict
    :return: Resultado da ação.
    :rtype: dict
    """

    account = database.find_account(data_deposit["Chave"])

    if account == None:
        response = {"Bem sucedido": False, "Justificativa": "Conta não encontrado"}
        return response

    response = account.deposit_balance(data_deposit["Valor"])
    return response


def withdraw(database: object, data_withdraw: dict) -> dict:
    """
    Saca um valor no saldo de uma conta indicada do armazenamento, se ela for encontrada. 
    O resultado da operação é retornado.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_withdraw: Dados do saque.
    :type data_withdraw: dict
    :return: Resultado da ação.
    :rtype: dict
    """

    account = database.find_account(data_withdraw["Chave"])

    if account == None:
        response = {"Bem sucedido": False, "Justificativa": "Conta não encontrado"}
        return response

    response = account.withdraw_balance(data_withdraw["Valor"])
    return response


def send_transfer(database: object, data_transfer: dict) -> dict:
    """
    Primeiro passo do envio em uma transferência, consistindo na transferência do saldo normal 
    de uma conta para o saldo bloqueado de conta. É verificado se a conta indicada está 
    no armazenamento, se sim, é verificado se ela tem saldo suficiente. É verificado 
    se a conta destinatária está no banco atual, se sim, ele mesmo faz todo o processo, 
    se não, é enviada a transferência para o outro banco. A retirada do dinheiro do 
    banco atual é do saldo disponível ao usuário, porém, o depósito, do banco atual ou 
    de outro banco, é para o saldo bloqueado.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_transfer: Dados da transferência.
    :type data_transfer: dict
    :return: Resultado da ação.
    :rtype: dict
    """

    if data_transfer["Chave remetente"] not in database.accounts:
        response = {"Bem sucedido": False, "Justificativa": "Conta do remetente não encontrada"}

    else:
        if database.accounts[data_transfer["Chave remetente"]].balance < float(data_transfer["Valor"]):
            response = {"Bem sucedido": False, "Justificativa": "Saldo insuficiente"}

        else:
            if data_transfer["Banco destinatário"] == database.ip_bank:

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
                        url = (f"http://{data_transfer['Banco destinatário']}:5060/receive_transfer")
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
    """
    Primeiro passo do recebimento de uma transferência, consistindo no recebimento de 
    um valor pra ser inserido no saldo bloqueado de uma conta. É verificado se a conta 
    está no armazenamento. O valor é depositado no saldo bloqueado da conta.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_transfer: Dados da transferência.
    :type data_transfer: dict
    :return: Resultado da ação.
    :rtype: dict
    """

    if data_transfer["Chave destinatário"] not in database.accounts:
        response = {"Bem sucedido": False, "Justificativa": "Conta do destinatário não encontrada"}
    
    else:
        database.accounts[data_transfer["Chave destinatário"]].deposit_blocked_balance(data_transfer["Valor"])
        response = {"Bem sucedido": True}
    
    return response


def send_release_transfer(database: object, data_transfer: dict) -> dict:
    """
    Segundo passo do envio de uma transferência, consistindo na liberação de um 
    valor no saldo bloqueado de uma conta para o saldo disponível ao usuário. É 
    verificado se o banco atual é o destinatário da transferência, se sim, ele 
    mesmo faz a alteração do saldo da conta destinatária, se não, ele envia para 
    o outro banco. O liberamento só ocorre se o pacote em que a transferência está 
    foi bem sucedido, se não, o valor não é liberado e a conta remetente recebe o 
    valor de volta no saldo disponível ao cliente.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_transfer: Dados da transferência.
    :type data_transfer: dict
    :return: Resultado da ação.
    :rtype: dict
    """
 
    if data_transfer["Banco destinatário"] == database.ip_bank:
        
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
                url = (f"http://{data_transfer['Banco destinatário']}:5060/receive_release_transfer")
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
    """
    Segundo passo do recebimento de uma transferência, consistindo na liberação 
    de um valor no saldo bloqueado de uma conta. É verificado se a conta 
    está no armazenamento. O valor só é somado no saldo disponível ao usuário 
    se o pacote que está essa transferência está foi bem sucedido.

    :param database: Armazenamento do banco.
    :type database: object
    :param data_transfer: Dados da transferência.
    :type data_transfer: dict
    :return: Resultado da ação.
    :rtype: dict
    """

    if data_transfer["Chave destinatário"] not in database.accounts:
        response = {"Bem sucedido": False, "Justificativa": "Conta do destinatário não encontrada"}
    
    else:
        database.accounts[data_transfer["Chave destinatário"]].withdraw_blocked_balance(data_transfer["Valor"])

        if data_transfer["Execução bem sucedida do pacote"] == True:
            database.accounts[data_transfer["Chave destinatário"]].deposit_balance(data_transfer["Valor"])
        
        response = {"Bem sucedido": True}
    
    return response
            