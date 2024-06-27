from flask import Flask, jsonify, json, request
import threading

import impl.bank_impl as bank_impl
import impl.register_impl as register_impl
import impl.token_impl as token_impl
from model.database import Database

app = Flask(__name__)
database = Database()


@app.route('/ready_for_connection', methods=['GET'])
def ready_for_connection():
    response = bank_impl.ready_for_connection(database)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/show', methods=['GET'])
def show_all():
    return jsonify(bank_impl.show_all(database)), 200



@app.route('/register/user', methods=['POST'])
def register_user():

    data_user = request.json
    response = register_impl.register_user(database, data_user)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/register/account', methods=['POST'])
def register_account():

    data_account = request.json
    response = register_impl.register_account(database, data_account)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/deposit', methods=['PATCH'])
def deposit_value():

    data_deposit = request.json
    response = bank_impl.deposit(database, data_deposit)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/withdraw', methods=['PATCH'])
def withdraw_value():

    data_withdraw = request.json
    response = bank_impl.withdraw(database, data_withdraw)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404



@app.route('/check_first_pass_token', methods=['GET'])
def check_first_pass_token():
    response = token_impl.check_first_pass_token(database)

    if response["Token está no sistema"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/token_pass', methods=['POST'])
def token_pass():
    data_token = request.json
    response = token_impl.receive_token(database, data_token)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/alert_token_duplicate', methods=['POST'])
def alert_token_duplicate():
    data_alert = request.json
    response = token_impl.receive_alert_token_duplicate(database, data_alert)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/request_package', methods=['PATCH'])
def request_package():
    data_package = request.json
    response = bank_impl.request_package(database, data_package)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404



''' RECEBIMENTO E TRANSFERÊNCIA
@app.route('/send_transfer/<string:id_sender>/<string:value>/<string:key_recipient>/<string:ip_bank>', methods=['PATCH'])
def send_transfer_value(id_sender: str, value: str, key_recipient: str, ip_bank: str):

    data_transfer = {"ID remetente": id_sender, "Valor": value, "Chave PIX": key_recipient, "IP banco": ip_bank}
    response = bank_impl.send_transfer(database, data_transfer)
    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/receive_transfer/<string:value>/<string:key_recipient>', methods=['PATCH'])
def receive_transfer_value(value: str, key_recipient: str):

    data_transfer = {"Valor": value, "Chave PIX": key_recipient}
    response = bank_impl.receive_transfer(database, data_transfer)
    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404
'''


def start():
    list_banks = ["5090", "5080", "5060"]
    threading.Thread(target=bank_impl.add_consortium, args=(database, list_banks,)).start()
    app.run(port=5070, host='0.0.0.0')