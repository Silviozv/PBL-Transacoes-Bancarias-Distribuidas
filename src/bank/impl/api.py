from flask import Flask, jsonify, json
import impl.bank_impl as impl

app = Flask(__name__)


@app.route('/', methods=['HEAD'])
def check_connection():

    return '', 200


@app.route('/show', methods=['GET'])
def show_all():

    return jsonify(impl.show_all()), 200


@app.route('/register/user/<string:cpf>/<string:name>', methods=['POST'])
def register_user(cpf: str, name: str):

    data_user = {"CPF": cpf, "Nome": name}
    response = impl.register_user(data_user)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/register/account/<string:type_account>/<string:cpfs>', methods=['POST'])
def register_account(type_account: str, cpfs: str):

    type_account = type_account.split("-")
    cpfs = cpfs.split('-')
    data_account = {"Tipo de conta": type_account, "CPFs": cpfs}
    response = impl.register_account(data_account)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/deposit/<string:id>/<string:value>', methods=['PATCH'])
def deposit_value(id: str, value: str):

    response = impl.deposit(id, value)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/withdraw/<string:id>/<string:value>', methods=['PATCH'])
def withdraw_value(id: str, value: str):

    response = impl.withdraw(id, value)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


def start():
    app.run(port=5070, host='0.0.0.0')