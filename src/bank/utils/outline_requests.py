import threading
import requests

def create_result_structure(quantity: int) -> dict:
    result_dict = {}
    for i in range(quantity):
        result_dict[i] = {"Terminado": False, "Resposta": None}
    return result_dict

def send_request(database: object, url: str, ip_bank: str, data: dict, http_method: str, result_dict: dict, index: str):
    try:
        if http_method == "GET":
            response = requests.get(url, json=data, timeout=5)
        elif http_method == "POST":
            response = requests.post(url, json=data, timeout=5)
        elif http_method == "PATCH":
            response = requests.patch(url, json=data, timeout=5)

        #if url == (f"http://{ip_bank}:5060/ready_for_connection") and response.status_code != 200:
        if url == (f"http://{database.ip_bank}:{ip_bank}/ready_for_connection") and response.status_code != 200:
            raise requests.exceptions.ConnectionError
        
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
        with database.lock:
            database.banks_recconection[ip_bank] = True
        threading.Thread(target=database.loop_reconnection, args=(ip_bank,)).start()
        response = {"Bem sucedido": False, "Justificativa": "Banco desconectado"}

    result_dict[index]["Resposta"] = response
    result_dict[index]["Terminado"] = True