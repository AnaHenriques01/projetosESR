from datetime import datetime, timedelta
import re
import threading
from time import sleep, perf_counter


# ----------------------- oNode -----------------------

command = '[10.0.0.1 : 10.0.0.2 , 10.0.0.3] [10.0.0.2 : 10.0.0.3, 10.0.0.6]'

my_id = 'oNode1'
is_bigNode = False
connections = {}

# vizinhos['NodoA'] = ['NodoB', 'NodoC']
# (1,A), (A, B), (A, C)
local_info_index = {
    'C': 0,
    'B': 1,
    'A': 2,
}

# tabela[index] = (nodo, tempo, last_refresh, is_server, is_bigNode, fastest_path)
local_info = [
    {
        'nodo': 'C',
        'tempo': 10,
        'n_saltos': 2,
        'last_refresh': datetime.now(),
        'is_server': True,
        'is_bigNode': False,
        'fastest_path': ['A', 'C']
    },
    {
        'nodo': 'B',
        'tempo': 10,
        'n_saltos': 2,
        'last_refresh': datetime.now(),
        'is_server': False,
        'is_bigNode': False,
        'fastest_path': ['A', 'B']
    },
    {
        'nodo': 'A',
        'tempo': 5,
        'n_saltos': 1,
        'last_refresh': datetime.now(),
        'is_server': False,
        'is_bigNode': True,
        'fastest_path': ['A']
    }
]


def overlayNetwork(command):
    nodes = []
    pairs = re.findall("(?:\[(.*?)\])", command)  # ['A:B,C', 'B:C', 'C:D,E']
    neighbors = []  # [ (indA,indB,distanceAB), (indA,indB,distanceAC), (ind,C,distanceBC) ]
    for p in pairs:
        ips = re.split(r'\s*:\s*', p)  # 'C', 'D,E'
        interf1 = interface(ips[0], [], [])
        if not any(obj.ip == ips[0] for obj in nodes):
            nodes.append(interf1)
        ips2 = re.split(r'\s*,\s', ips[1])  # 'D', 'E'
        for next in ips2:
            interf2 = interface(next, [], [])
            if not any(obj.ip == next for obj in nodes):
                nodes.append(interf2)
            neighbors.append((getIndex(nodes, interf1.ip), (getIndex(nodes, interf2.ip))))
    return nodes, neighbors


def uiHandler():
    print('a iniciar client...')
    while (True):
        print('*doing client stuff*')
        sleep(2)


def refresh(tabela, tempo_recebido, true_sender, n_saltos, timestamps, tree_back_to_sender, is_server, is_bigNode):
    nodo, tempo = timestamps[0]
    delta = tempo_recebido - tempo

    if true_sender in local_info_index:
        sender_index = local_info_index[true_sender]

        # tabela[index] = (nodo, tempo, last_refresh, is_server, is_bigNode, fastest_path)
        tabela[sender_index]['last_refresh'] = datetime.now()
        if tabela[sender_index]['tempo'] > delta:
            tabela[sender_index]['tempo'] = delta
            tabela[sender_index]['fastest_path'] = tree_back_to_sender

        elif tabela[sender_index]['tempo'] == delta & tabela[sender_index]['saltos'] >= n_saltos:
            tabela[sender_index]['tempo'] = delta
            tabela[sender_index]['fastest_path'] = tree_back_to_sender
            tabela[sender_index]['saltos'] = n_saltos
    else:
        n = len(local_info_index)
        local_info_index[true_sender] = n
        tabela[n] = {
            'nodo': true_sender,
            'tempo': delta,
            'saltos': n_saltos,
            'last_refresh': datetime.now(),
            'is_server': is_server,
            'is_bigNode': is_bigNode,
            'fastest_path': tree_back_to_sender
        }
    return tabela


def forward_mensagem(true_sender, n_saltos, timestamps, tree_back_to_sender, is_server, is_bigNode):
    timestamps.append(my_id, datetime.now())

    new_tree = [my_id, tree_back_to_sender]
    return true_sender, n_saltos + 1, timestamps, new_tree, is_server, is_bigNode


def messageHandler():
    # flooding controlado
    for i in local_info:
        delta = datetime.now() - i['last_refresh']
        expired = timedelta(minutes=1)
        if delta > expired:
            nodo = i['nodo']
            # send to nodo mensagem
    pass


def networkHandler():
    # recebe e passa informação

    # if is_bigNode : armazena tabela de ficheiros locais da sua subrede
    pass


def serverHandler():
    print('a iniciar servidor servidor...')
    refresh_table = threading.Thread(target=messageHandler, args=())
    refresh_table.start()

    network = threading.Thread(target=networkHandler, args=())
    network.start()

    refresh_table.join()
    network.join()


start_time = perf_counter()

# task goes here

end_time = perf_counter()
print(f'It took {end_time - start_time: 0.2f} second(s) to complete.')
threads = []

media_player = threading.Thread(target=uiHandler, args=())
media_player.start()

servidor = threading.Thread(target=uiHandler, args=())
servidor.start()

servidor.join()
media_player.join()
