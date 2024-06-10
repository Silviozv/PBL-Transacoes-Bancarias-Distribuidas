from flask import Flask, jsonify, json, request
import impl.bank_impl as impl

app = Flask(__name__)


@app.route('/', methods=['HEAD'])
def check_connection():

    return '', 200


@app.route('/show', methods=['GET'])
def show_all():

    return jsonify(impl.show_all()), 200


@app.route('/register/user', methods=['POST'])
def register_user():

    data_user = request.json
    response = impl.register_user(data_user)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/register/account', methods=['POST'])
def register_account():

    data_account = request.json
    response = impl.register_account(data_account)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/deposit', methods=['PATCH'])
def deposit_value():

    data_deposit = request.json
    response = impl.deposit(data_deposit)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/withdraw', methods=['PATCH'])
def withdraw_value():

    data_withdraw = request.json
    response = impl.withdraw(data_withdraw)

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/request_add_bank', methods=['POST'])
def request_add_bank():

    data_request = request.json
    response = impl.request_add_bank(data_request["IP banco"], data_request["IPs registrados no remetente"])

    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/verify_leadership', methods=['GET'])
def verify_leadership():

    response = impl.verify_leadership()

    if response["Liderança"] == True:
        return response, 200
    else:
        return response, 404


@app.route('/election_request', methods=['PATCH'])
def election_request():

    data_election = request.json




################################################################
@app.route('/send_transfer/<string:id_sender>/<string:value>/<string:key_recipient>/<string:ip_bank>', methods=['PATCH'])
def send_transfer_value(id_sender: str, value: str, key_recipient: str, ip_bank: str):

    data_transfer = {"ID remetente": id_sender, "Valor": value, "Chave PIX": key_recipient, "IP banco": ip_bank}
    response = impl.send_transfer(data_transfer)
    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/receive_transfer/<string:value>/<string:key_recipient>', methods=['PATCH'])
def receive_transfer_value(value: str, key_recipient: str):

    data_transfer = {"Valor": value, "Chave PIX": key_recipient}
    response = impl.receive_transfer(data_transfer)
    if response["Bem sucedido"] == True:
        return jsonify(response), 200
    else:
        return jsonify(response), 404

################################################################

def start():
    app.run(port=5070, host='0.0.0.0')