from flask import Flask, jsonify, json
import impl.bank_impl as impl

app = Flask(__name__)

@app.route('/',methods=['HEAD'])
def check_connection():

    return '', 200

@app.route('/register/<string:type_account>/<string:names_user>/<string:cpfs>',methods=['POST'])
def register_account(type_account: str, names_user: str, cpfs: str):



    return '', 200

def start():
    app.run(port=5070,host='0.0.0.0')