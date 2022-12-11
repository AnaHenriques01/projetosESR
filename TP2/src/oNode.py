import datetime
import json
import os
import re
import socket
import struct
import sys
import threading
import time
from bson import json_util
import handlers.oClient as client
import handlers.oServer as server
from Streaming.ServerStreamer import ServerStreamer

file_id = sys.argv[1]

current_pwd_path = os.path.dirname(os.path.abspath(__file__))
video_pwd_path = (re.findall("(?:(.*?)src)", current_pwd_path))[0]
path_to_topologia = os.path.join(video_pwd_path, "overlay/topologia" + str(file_id) + ".json")
path_to_node_info = os.path.join(video_pwd_path, "overlay/node_info" + str(file_id) + ".json")

c = open(path_to_topologia)
i = open(path_to_node_info)

info = json.load(i)
connections = json.load(c)

# ----------------------- Variaveis locais -----------------------

node_id = info['node_id']
my_port = int(info['my_port'])
is_bigNode = info['is_bigNode']  # True / False
is_server = info['is_server']  # True / False
ports = info['ports']  # ({'ip': '192.168.1.3', 'port': 5000})

local_info = []# mirrors message structure

# Número max de saltos para o flooding
max_hops = 20

# Número max de conexões
MAX_CONN = 25

# Estrutura da Mensagem a enviar aos nodos aquando do Flooding
message = {
    'nodo': str(node_id),
    'port': str(my_port),
    'tempo': str([datetime.time()]),
    'saltos': "0",
    'last_refresh': str(datetime.time()),
    'is_server': str(is_server),
    'is_bigNode': str(is_bigNode),
    'nearest_server': str([])
}

"""
Nesta Format String, o caractere > indica que os dados estão em big-endian byte order,
Os códigos de formatação individuais especificam os tipos dos campos em 'mensagem'.
O código de formatação '64s' indica que os campos 'nodo' e 'port' são strings de até 64 caracteres,
O código de formatação '16s' indica que os campos 'tempo' e 'last_refresh' são objetos de data e hora de até 16 chars
O código de formatação 'L' indica que o campo 'saltos' é um inteiro sem sinal de 32 bits,
O código de formatação '?' indica que os campos 'is_server' e 'is_bigNode' são booleanos,
O código de formatação '64s' no final indica que o campo 'nearest_server' é uma lista de strings de até 64 chars cada
"""

PACKET_FORMAT = ">64s64s16sL16s??64s"


# ----------------------- Enviar mensagens -----------------------

def send_message(nodo, m):
    print(f"\n\n[{nodo['ip']}: {nodo['port']}] is sending a message \n{m}\n\n")

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((node_id, my_port))

    message_data = json.dumps(m, default=json_util.default)
    s.sendto(message_data.encode(), (nodo['ip'], int(nodo['port'])))
    s.close()


def flood():
    for entry in ports:
        send_message(entry, message)


def refresh_message():
    message['tempo'] = [datetime.datetime.now()]
    message['last_refresh'] = datetime.datetime.now()


def refresh():
    print("its happening")
    flood()
    while True:
        time.sleep(30)
        refresh_message()
        flood()


# ----------------------- Receber mensagens -----------------------

def check_and_register(m):
    if m['is_server'] == "True" or m['is_big_node'] == "True":
        delta = m['tempo'][1]

        if message['nearest_server'] != [] or (message['nearest_server'][0][2] >= (m['nearest_server'][0][2] + delta)
                                             or (message['nearest_server'][0][2] == m['nearest_server'][0][2]
                                                 + delta and m['saltos'] < message['saltos'])):
            message['nearest_server'] = [(m['nodo'], m['port'], m['tempo'][0] + delta)]


def receive_message(m_encoded):
    m = m_encoded.decode()
    print(f"[{node_id}: {my_port}] recebeu: \n{m}.\n")

    delta = datetime.datetime.now() - m['tempo'][0]
    m['tempo'][1] = delta

    if m['nodo'] == node_id:
        return

    if m['saltos'] >= max_hops:
        return

    # Se o nodo da mensagem já está na tabela local, atualiza
    if any(msg['nodo'] == m['nodo'] for msg in local_info):
        existing_message = next(msg for msg in local_info if msg['nodo'] == m['nodo'])
        existing_message.update(m)
        existing_message['last_refresh'] = datetime.time()
    else:
        m['saltos'] += 1
        m['last_refresh'] = datetime.time()
        local_info.append(m)

    # Verifica e Regista a informação do nodo na lista de servidores mais próximos
    check_and_register(m)

    flood()


def listening():
    s = socket.socket()
    s.bind((node_id, my_port))

    while True:
        data, address = s.recvfrom(1024)
        m0 = data.decode()

        packet_data = struct.unpack(PACKET_FORMAT, data)

        if 'nodo' not in packet_data:
            break

        m = json.loads(m0)
        receive_message(m)

    s.close()


def message_handler():
    time.sleep(30)
    send = threading.Thread(target=refresh, args=())
    rec = threading.Thread(target=listening, args=())

    rec.start()
    send.start()

    rec.join()
    send.join()


# ----------------------- oNode.py -----------------------

lock = threading.Lock()

threads = []

refresh_table = threading.Thread(target=message_handler, args=())
refresh_table.start()

if is_server == "True" or is_bigNode == "True":
    # Escuta por pedidos e envia ficheiros
    streaming = threading.Thread(target=server.stream, args=(node_id,my_port,is_server,is_bigNode,MAX_CONN))
    streaming.start()

else:
    # Faz pedidos
    media_player = threading.Thread(target=client.ui_handler, args=(local_info, node_id, my_port, lock))
    media_player.start()

refresh_table.join()

if is_server == "True" or is_bigNode == "True":
    streaming.join()

else:
    media_player.join()