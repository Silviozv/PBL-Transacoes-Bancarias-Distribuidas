import requests
import os
import re

#teste
import socket
ip_teste = socket.gethostbyname(socket.gethostname())

def start():
    utils = {"Formato padrão de IP": re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')}

    info = {}
    info['Menu atual'] = 'Inicial'
    info['IP servidor'] = ''
    info['Nome usuário'] = ''
    info['CPF usuário'] = ''
    info['Banco atual'] = ''
    info['Informação a ser exibida'] = 'Gerenciador iniciado'
    info['Tipo de informação a ser exibida'] = ''
    info['Opção'] = ''

    while ( info['Menu atual'] != ''):

        show_screen(info)

        info['Opção'] = input("\n  > ").strip()
        process_option(info, utils)

        clear_terminal()

    return 0 


def show_screen( info: dict):
    print("\n+-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-+")
    print("|                           GERENCIAMENTO DE CONTAS                           |")
    print("+-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-+")

    if ( info['Menu atual'] == 'Inicial'):
        menu = {'1': 'FAZER LOGIN', '2': 'FAZER CADASTRO', '3': 'SAIR'}
    elif ( info['Menu atual'] == 'Usuário logado'):
        menu = {'1': 'CRIAR CONTA', '2': 'CONSULTAR CONTAS NO CONSÓRCIO', '3': 'VOLTAR'}
    elif ( info['Menu atual'] == 'Criando conta'):
        menu = {'1': 'FÍSICA PESSOAL', '2': 'FÍSICA CONJUNTA', '3': 'JURÍDICA', '4': 'VOLTAR'}

    print("+-----------------------------------------------------------------------------+")
    print("|" + " " * 77 + "|")
    for key in menu.keys():
        text = f"[ {key} ] {menu[key]}"
        space_before = 22
        space_after = 77 - (len(text) + space_before)
        print("|" + " " * space_before + text + " " * space_after + "|")
    print("|" + " " * 77 + "|")
    print("+-----------------------------------------------------------------------------+")

    if ( info['Informação a ser exibida'] != ''):

        print("|" + " " * 77 + "|")

        if ( type(info['Informação a ser exibida']) == str):
            text = info['Informação a ser exibida']
            space_before = (77 - len(text)) // 2
            space_after = 77 - (len(text) + space_before)
            print("|" + " " * space_before + text + " " * space_after + "|")

            print("|" + " " * 77 + "|")

        elif ( type(info['Informação a ser exibida']) == list):
            for i in range(len(info['Informação a ser exibida'])):
                text = f"{i+1}: {info['Informação a ser exibida'][i]}"
                space_before = 1
                space_after = 77 - (len(text) + space_before)
                print("|" + " " * space_before + text + " " * space_after + "|")

            print("|" + " " * 77 + "|")

        elif ( type(info['Informação a ser exibida']) == dict):
            if info['Tipo de informação a ser exibida'] == 'Contas do usuário':

                for key in info['Informação a ser exibida'].keys():

                    text = f"- IP do banco: {key}"
                    space_after = 77 - (len(text) + 4)
                    print("|    " + text + " " * space_after + "|")

                    print("|" + " " * 77 + "|")

                    for i in range(len(info['Informação a ser exibida'][key])):

                        text = f"ID da conta: {info['Informação a ser exibida'][key][i]['Chave']}"
                        space_after = 77 - (len(text) + 6)
                        print("|      " + text + " " * space_after + "|")

                        if len(info['Informação a ser exibida'][key][i]['Tipo de conta']) == 1:
                            text = f"Tipo de conta: {info['Informação a ser exibida'][key][i]['Tipo de conta'][0]}"
                        else:
                            text = f"Tipo de conta: {info['Informação a ser exibida'][key][i]['Tipo de conta'][0]} {info['Informação a ser exibida'][key][i]['Tipo de conta'][1]}"
                        space_after = 77 - (len(text) + 6)
                        print("|      " + text + " " * space_after + "|")

                        text = f"CPFs vinculados: {info['Informação a ser exibida'][key][i]['CPFs'][0]}"
                        for j in range(1, len(info['Informação a ser exibida'][key][i]['CPFs'])):
                            text = text + f", {info['Informação a ser exibida'][key][i]['CPFs'][j]}"
                        space_after = 77 - (len(text) + 6)
                        print("|      " + text + " " * space_after + "|")

                        text = f"Saldo: {info['Informação a ser exibida'][key][i]['Saldo']}"
                        space_after = 77 - (len(text) + 6)
                        print("|      " + text + " " * space_after + "|")

                        print("|" + " " * 77 + "|")



        print("+-----------------------------------------------------------------------------+")


def process_option(info: dict, utils: dict) -> dict:


    if (info['Menu atual'] == 'Inicial'):

        if (info['Opção'] == '1'):
            try:
                cpf = input("\n  - CPF: ").strip()
                #if cpf.isdigit() == False or len(cpf) != 11:
                #    raise ValueError("CPF inválido")
                ip_bank = input("  - IP do banco: ").strip()
                #if utils["Formato padrão de IP"].match(ip_bank) == False:
                #    raise ValueError("IP inválido")
            
                data = {"CPF": cpf}
                #url = (f"http://{ip_bank}:5060/register/user")
                url = (f"http://{ip_teste}:{ip_bank}/check/user")
                response = requests.get(url, json=data)
                status_code = response.status_code
                response = response.json()
                
                if status_code == 200:
                    info['Menu atual'] = 'Usuário logado'
                    info['Nome usuário'] = response["Nome do usuário"]
                    info['CPF usuário'] = cpf
                    info['Banco atual'] = ip_bank
                    info['Informação a ser exibida'] = 'Login realizado'
                else:
                    info['Informação a ser exibida'] = 'Usuário não encontrado'

            except (ValueError) as e:
                info['Informação a ser exibida'] = str(e)
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                info['Informação a ser exibida'] = 'Não foi possível fazer a conexão'

        elif (info['Opção'] == '2'):
            try:
                name = input("\n  - Nome: ").strip()
                if name.isalpha() == False:
                    raise ValueError("Nome inválido")
                cpf = input("  - CPF: ").strip()
                #if cpf.isdigit() == False or len(cpf) != 11:
                #    raise ValueError("CPF inválido")
                ip_bank = input("  - IP do banco: ").strip()
                #if utils["Formato padrão de IP"].match(ip_bank) == False:
                #    raise ValueError("IP inválido")

                data = {"Nome": name, "CPF": cpf}
                #url = (f"http://{ip_bank}:5060/register/user")
                url = (f"http://{ip_teste}:{ip_bank}/register/user")
                response = requests.post(url, json=data)
                status_code = response.status_code
                response = response.json()

                if status_code == 200:
                    info['Informação a ser exibida'] = 'Usuário cadastrado'
                elif "Bem sucedido" in response.keys():
                    info['Informação a ser exibida'] = response['Justificativa']

            except (ValueError) as e:
                info['Informação a ser exibida'] = str(e)
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                info['Informação a ser exibida'] = 'Não foi possível fazer a conexão'
        
        elif (info['Opção'] == '3'):
            info['Menu atual'] = ''

        else:
            info['Informação a ser exibida'] = 'Opção inválida'


    elif (info['Menu atual'] == 'Usuário logado'):

        if (info['Opção'] == '1'):
            info['Menu atual'] = 'Criando conta'
            info['Informação a ser exibida'] = 'Escolha o tipo de conta'

        elif (info['Opção'] == '2'):
            data = {"CPF usuário": info['CPF usuário']}
            #url = (f"http://{info['Banco atual']:5060/get/account/consortium")
            url = (f"http://{ip_teste}:{info['Banco atual']}/get/account/consortium")
            response = requests.get(url, json=data)
            status_code = response.status_code

            if status_code == 200:
                response = response.json()
                info['Tipo de informação a ser exibida'] = 'Contas do usuário'
                info['Informação a ser exibida'] = response["Contas"]
            else:
                info['Informação a ser exibida'] = 'Nenhuma conta foi encontrada'

        elif (info['Opção'] == '3'):
            info['Menu atual'] = 'Inicial'
            info['Informação a ser exibida'] = ''

        else:
            info['Informação a ser exibida'] = 'Opção inválida'


    elif (info['Menu atual'] == 'Criando conta'):

        if (info['Opção'] == '1'):
            try:
                data = {"CPFs": [info['CPF usuário']], "Tipo de conta": ["Física","Pessoal"]}
                #url = (f"http://{info['Banco atual']:5060/register/account")
                url = (f"http://{ip_teste}:{info['Banco atual']}/register/account")
                response = requests.post(url, json=data)
                status_code = response.status_code
                response = response.json()

                if status_code == 200:
                    info['Informação a ser exibida'] = 'Conta física pessoal criada'
                elif response["Justificativa"] == "O usuário já possui uma conta física":
                    info['Informação a ser exibida'] = 'Conta física pessoal já existe'
                elif response["Justificativa"] == "Usuário não encontrado":
                    info['Menu atual'] = 'Inicial'
                    info['Informação a ser exibida'] = response["Justificativa"]

            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                info['Informação a ser exibida'] = 'Conexão interrompida'

        elif (info['Opção'] == '2' or info['Opção'] == '3'):
            try:
                quantity = input("\n  - Quantidade de pessoas vinculadas: ").strip()
                if quantity.isdigit() == False or int(quantity) <= 1:
                    raise ValueError("Quantidade inválida")
                elif int(quantity) > 4:
                    raise ValueError("Só permitido até 4 contas vinculadas") 
                
                cpfs = []
                print()
                for i in range(int(quantity)):
                    cpf = input(f"  - CPF do usuário {i+1}: ").strip()
                    #if cpf.isdigit() == False or len(cpf) != 11:
                    #    raise ValueError("CPF inválido")
                    if cpf in cpfs:
                        raise ValueError("CPFs duplicados")
                    cpfs.append(cpf)

                if info['CPF usuário'] not in cpfs:
                    raise ValueError("Usuário não incluido")

                if info['Opção'] == '2':
                    data = {"CPFs": cpfs, "Tipo de conta": ["Física","Conjunta"]}
                elif info['Opção'] == '3':
                    data = {"CPFs": cpfs, "Tipo de conta": ["Jurídica"]}

                #url = (f"http://{info['Banco atual']:5060/register/account")
                url = (f"http://{ip_teste}:{info['Banco atual']}/register/account")
                response = requests.post(url, json=data)
                status_code = response.status_code
                response = response.json()
            
                if status_code == 200:
                    if info['Opção'] == '2':
                        info['Informação a ser exibida'] = 'Conta física conjunta criada'
                    if info['Opção'] == '3':
                        info['Informação a ser exibida'] = 'Conta jurídica criada'
                elif response["Justificativa"] == "Usuário não encontrado":
                    info['Informação a ser exibida'] = 'Algum dos usuários não foi encontrado'
            
            except (ValueError) as e:
                info['Informação a ser exibida'] = str(e)
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                info['Informação a ser exibida'] = 'Conexão interrompida'
        
        elif (info['Opção'] == '4'):
            info['Menu atual'] = 'Usuário logado'
            info['Informação a ser exibida'] = ''
        
        else:
            info['Informação a ser exibida'] = 'Opção inválida'








def clear_terminal():
    if os.name == 'nt':  
        os.system('cls')
    else: 
        os.system('clear')