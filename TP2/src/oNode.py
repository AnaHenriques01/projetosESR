import json
import datetime
import threading
import sys
import socket
import time

from src.handlers.client import ui_handler
from src.handlers.server import server_handler

file_id = str(sys.argv)[0]

c = open(f'topologia{file_id}.json')
i = open(f'node_info{file_id}.json')

info = json.load(i)
connections = json.load(c)

# ----------------------- variaveis locais -----------------------

node_id = info['node_id']
my_port = info['my_port']
is_bigNode = info['is_bigNode']  # True / False
is_server = info['is_server']  # True / False
ports = info['ports']  # ({'ip': '192.168.1.3', 'port': 5000})

local_info = []  # mirrors message structure

# número max de saltos para o flooding
max_hops = 20

# The message that will be sent to other nodes
message = {
    'nodo': node_id,
    'port': my_port,
    'tempo': datetime.time(),
    'saltos': 0,
    'last_refresh': datetime.time(),
    'is_server': is_server,
    'is_bigNode': is_bigNode,
    'nearest_server': []
}


# ----------------------- enviar mensagens -----------------------

def send_message(nodo, message):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(nodo['ip'], nodo['port'])

    # Serialize the message using JSON
    message_data = json.dumps(message)
    s.send(message_data)
    s.close()


def flood():
    for entry in ports:
        send_message(entry, message)


def refresh_message():
    message['tempo'] = time.time()
    message['last_refresh'] = time.time()


def refresh():
    flood()
    while True:
        time.sleep(30)
        refresh_message()
        flood()


# ----------------------- receber mensagens -----------------------

def get_faster_path():
    return [message['fastest_path'][-1]]


def new_faster_path(param):
    pass


def receive_message(nodo, m):
    delta = time.time() - m['tempo']
    m['tempo'] = delta

    if m['nodo'] == node_id:
        return

    if m['saltos'] >= max_hops:
        return

    if new_faster_path(m['fastest_path']):
        message['fastest_path'] = m['fastest_path']
    else:
        m['fastest_path'] = get_faster_path()

    # If the message is not in the list of known messages, add it and update the message
    if m not in local_info:
        m['saltos'] += 1
        m['last_refresh'] = time.time()

        # set the appropriate flags in the message
        m['is_server'] = is_server
        m['is_big_node'] = is_bigNode

        local_info.append(m)

    # Flood the updated message to all known peers
    flood()


def listen_to(nodo):
    s = socket.socket()
    s.bind(nodo['ip'], nodo['port'])

    # Start listening for incoming connections
    s.listen(1)
    conn, addr = s.accept()

    while True:
        data = conn.recv(1024)

        if not data:
            break

        m = json.loads(data)
        receive_message(nodo, m)

    conn.close()


def listening():
    for node in ports:
        t = threading.Thread(target=listen_to, args=(node,))
        t.start()


def message_handler():
    send = threading.Thread(target=refresh, args=())
    rec = threading.Thread(target=listening(), args=())

    send.start()
    rec.start()

    send.join()
    rec.join()


# ----------------------- oNode.py -----------------------
lock = threading.Lock()

threads = []

media_player = threading.Thread(target=ui_handler, args=(local_info, node_id))
media_player.start()

servidor = threading.Thread(target=server_handler, args=(ports, node_id))
servidor.start()

servidor.join()
media_player.join()
