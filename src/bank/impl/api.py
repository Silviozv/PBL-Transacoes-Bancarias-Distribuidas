""" 
Módulo contendo os caminhos a função relacionados a implementação da API.
"""

from flask import Flask, jsonify, request
import threading
import re

import impl.bank_impl as bank_impl
import impl.register_impl as register_impl
import impl.token_impl as token_impl
import impl.package_impl as package_impl
from model.database import Database


""" 
Declaração da API e do objeto contendo o armazenamento do banco.
"""
app = Flask(__name__)
database = Database()


@app.route('/ready_for_connection', methods=['GET'])
def ready_for_connection():
    """
    Retorna se o banco está disponível para conexão.
    """

    response = bank_impl.ready_for_connection(database)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/register/user', methods=['POST'])
def register_user():
    """
    Registra um usuário no armazenamento do banco.
    """

    data_user = request.json
    response = register_impl.register_user(database, data_user)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/check/user', methods=['GET'])
def check_user():
    """
    Checa se o usuário indicado está no armazenamento do banco.
    """

    data_check = request.json
    response = bank_impl.check_user(database, data_check)

    if response["Usuário encontrado"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/register/account', methods=['POST'])
def register_account():
    """
    Registra uma conta no armazenamento do banco.
    """

    data_account = request.json
    response = register_impl.register_account(database, data_account)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404
    

@app.route('/get/account/consortium', methods=['GET'])
def get_account_consortium():
    """
    Retorna os dados das contas do usuário em todos os bancos do consórcio.
    """

    data_user = request.json
    response = bank_impl.get_account_consortium(database, data_user)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/get/account/user', methods=['GET'])
def get_account_by_user():
    """
    Retorna as contas do usuário indicado armazenadas no banco.
    """

    data_user = request.json
    response = bank_impl.get_account_by_user(database, data_user)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/check/account/id', methods=['GET'])
def check_account_by_id():
    """
    Checa se a conta indicada está no armazenamento do banco pelo ID.
    """

    data_account = request.json
    response = bank_impl.check_account_by_id(database, data_account)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/deposit', methods=['PATCH'])
def deposit_value():
    """
    Deposita um valor em uma conta do banco.
    """

    data_deposit = request.json
    response = bank_impl.deposit(database, data_deposit)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/withdraw', methods=['PATCH'])
def withdraw_value():
    """
    Saca um valor em uma conta do banco.
    """

    data_withdraw = request.json
    response = bank_impl.withdraw(database, data_withdraw)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404



@app.route('/check_first_pass_token', methods=['GET'])
def check_first_pass_token():
    """
    Checa se o token já está passando no sistema.
    """

    response = token_impl.check_first_pass_token(database)

    if response["Token está no sistema"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/token_pass', methods=['POST'])
def token_pass():
    """
    Recebimento do token.
    """

    data_token = request.json
    response = token_impl.receive_token(database, data_token)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/alert_problem_detected', methods=['POST'])
def alert_problem_detected():
    """
    Recebimento de alerta de problema detectado na passagem do token no sistema.
    """

    data_alert = request.json
    response = token_impl.receive_problem_alert(database, data_alert)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/request_package', methods=['PATCH'])
def request_package():
    """
    Recebimento de um pacote de transferências.
    """

    data_package = request.json
    response = package_impl.request_package(database, data_package)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/send_transfer', methods=['PATCH'])
def send_transfer_value():
    """
    Recebimento de requisição para transferir um valor de uma conta.
    """

    data_transfer = request.json
    response = bank_impl.send_transfer(database, data_transfer)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/receive_transfer', methods=['PATCH'])
def receive_transfer_value():
    """
    Recebimento de um valor para ser adicionado ao saldo bloqueado de uma conta.
    """

    data_transfer = request.json
    response = bank_impl.receive_transfer(database, data_transfer)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/send_release_transfer', methods=['PATCH'])
def send_release_transfer_value():
    """
    Recebimento de requisição para enviar aviso de liberação de valor no saldo bloqueado 
    de uma conta.
    """

    data_transfer = request.json
    response = bank_impl.send_release_transfer(database, data_transfer)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/receive_release_transfer', methods=['PATCH'])
def receive_release_transfer_value():
    """
    Recebimento de requisição para liberar o saldo bloqueado de uma conta.
    """

    data_transfer = request.json
    response = bank_impl.receive_release_transfer(database, data_transfer)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404
    

@app.route('/confirm_package_execution', methods=['PATCH'])
def confirm_package_execution():
    """
    Recebimento da confirmação de execução de um pacote.
    """

    data_confirm = request.json
    response = package_impl.confirm_package_execution(database, data_confirm)
    
    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/check_it_has_token', methods=['GET'])
def check_it_has_token():
    """
    Checa se o token está no banco.
    """

    response = token_impl.check_it_has_token(database)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


def start():
    """
    Inicialização da API. É exibido o IP atual do banco. É pedida a quantidade de 
    bancos do consórcio, em seguida, é solicitado o IP de cada um. São iniciadas as
    funções de contagem do tempo sem receber o token e de inicialização dos dados 
    do banco, depois, a API é iniciada.
    """

    print(f"\nIP atual: {database.ip_bank}")

    quantity = input("\nQuantidade de bancos do consórcio: ")
    try:
        quantity = int(quantity)

        if quantity <= 0:
            raise ValueError

        list_banks = []
        print()
        for i in range(quantity):
            bank = input(f"Banco {i+1}: ")
            if (not (re.match(r'^(\d{1,3}\.){3}\d{1,3}$', bank))):
                raise ValueError
            list_banks.append(bank)

        print()
        threading.Thread(target=token_impl.count_time_token, args=(database, len(list_banks) * 10,)).start()
        threading.Thread(target=bank_impl.add_consortium, args=(database, list_banks,)).start()
        app.run(port=5060, host='0.0.0.0')

    except ValueError:
        print("Dado inválido.")