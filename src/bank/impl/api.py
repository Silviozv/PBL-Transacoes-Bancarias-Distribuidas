from flask import Flask, jsonify, request
import threading
import re

import impl.bank_impl as bank_impl
import impl.register_impl as register_impl
import impl.token_impl as token_impl
import impl.package_impl as package_impl
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


@app.route('/register/user', methods=['POST'])
def register_user():

    data_user = request.json
    response = register_impl.register_user(database, data_user)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/check/user', methods=['GET'])
def check_user():

    data_check = request.json
    response = bank_impl.check_user(database, data_check)

    if response["Usuário encontrado"] == True:
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
    

@app.route('/get/account/consortium', methods=['GET'])
def get_account_consortium():

    data_user = request.json
    response = bank_impl.get_account_consortium(database, data_user)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/get/account/user', methods=['GET'])
def get_account_by_user():

    data_user = request.json
    response = bank_impl.get_account_by_user(database, data_user)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/check/account/id', methods=['GET'])
def check_account_by_id():

    data_account = request.json
    response = bank_impl.check_account_by_id(database, data_account)

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


@app.route('/alert_problem_detected', methods=['POST'])
def alert_problem_detected():
    data_alert = request.json
    response = token_impl.receive_problem_alert(database, data_alert)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/request_package', methods=['PATCH'])
def request_package():
    data_package = request.json
    response = package_impl.request_package(database, data_package)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/send_transfer', methods=['PATCH'])
def send_transfer_value():
    data_transfer = request.json
    response = bank_impl.send_transfer(database, data_transfer)
    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/receive_transfer', methods=['PATCH'])
def receive_transfer_value():
    data_transfer = request.json
    response = bank_impl.receive_transfer(database, data_transfer)
    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/send_release_transfer', methods=['PATCH'])
def send_release_transfer_value():
    data_transfer = request.json
    response = bank_impl.send_release_transfer(database, data_transfer)
    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/receive_release_transfer', methods=['PATCH'])
def receive_release_transfer_value():
    data_transfer = request.json
    response = bank_impl.receive_release_transfer(database, data_transfer)
    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404
    

@app.route('/confirm_package_execution', methods=['PATCH'])
def confirm_package_execution():
    data_confirm = request.json
    response = package_impl.confirm_package_execution(database, data_confirm)
    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/check_it_has_token', methods=['GET'])
def check_it_has_token():
    response = token_impl.check_it_has_token(database)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


def start():
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