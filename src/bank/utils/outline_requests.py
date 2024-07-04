""" 
Módulo contendo as funções de esboço de envio de requisições HTTP.
"""

import threading
import requests


def create_result_structure(quantity: int) -> dict:
    """
    Cria estrutura para requisições separadas em threads indicarem quando foi terminado o envio 
    da mensagens.

    :param quantity: Quantidade de requisições que serão feitas.
    :type quantity: int
    :return: Estrutura com as indicações para as requisições setarem após seu término.
    :rtype: dict
    """

    result_dict = {}
    for i in range(quantity):
        result_dict[i] = {"Terminado": False, "Resposta": None}

    return result_dict


def send_request(database: object, url: str, ip_bank: str, data: dict, http_method: str, result_dict: dict, index: str):
    """
    Esboço para envio de uma requisição HTTP. Quando o envio é terminado é indicado na estrutura 
    para processos em outros planos terem acesso ao término e ao retorno da requisição.

    :param database: Armazenamento do banco.
    :type database: object
    :param url: URL da requisição.
    :type url: str
    :param ip_bank: IP do banco que vai receber a requisição.
    :type ip_bank: str
    :param data: Dados a serem enviados com a requisição.
    :type data: dict
    :param http_method: Método HTTP da requisição.
    :type http_method: str
    :param result_dict: Estrutura para indicar o término do envio da requisição e o retorno dela.
    :type result_dict: dict
    :param index: Chave do processo atual na estrutura.
    :type index: str
    """

    try:
        if http_method == "GET":
            response = requests.get(url, json=data, timeout=5)
        elif http_method == "POST":
            response = requests.post(url, json=data, timeout=5)
        elif http_method == "PATCH":
            response = requests.patch(url, json=data, timeout=5)

        if url == (f"http://{ip_bank}:5060/ready_for_connection") and response.status_code != 200:
            raise requests.exceptions.ConnectionError
        
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
        with database.lock:
            database.banks_recconection[ip_bank] = True
        threading.Thread(target=database.loop_reconnection, args=(ip_bank,)).start()
        response = {"Bem sucedido": False, "Justificativa": "Banco desconectado"}

    result_dict[index]["Resposta"] = response
    result_dict[index]["Terminado"] = True