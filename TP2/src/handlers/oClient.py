import os
import re
from tkinter import Tk
from time import sleep
from Streaming.ClientStreamer import ClientStreamer


def ui_handler(message, node_id, my_port, lock):
    print(f'\nA iniciar cliente {node_id}:{my_port}...')

    while not message['nearest_server']:
        sleep(1)

    while True:
        
        if os.environ.get('DISPLAY', '') == '':
            print('Nenhum display encontrado... Usar DISPLAY :0.0')
            os.environ.__setitem__('DISPLAY', ':0.0')

        current_pwd_path = os.path.dirname(os.path.abspath(__file__))
        video_pwd_path = (re.findall("(?:(.*?)src)", current_pwd_path))[0]
        filename = "movie.Mjpeg"

        path_to_filename = os.path.join(video_pwd_path, "play/" + str(filename))

        root = Tk()

        lock.acquire()

        print("nearest_server: " + str(message['nearest_server']))

        if message['nearest_server']:
            server_addr, server_port = message['nearest_server'][0][0], int(message['nearest_server'][0][1])
            rtp_address, rtp_port = (node_id, my_port)
            lock.release()

            # Create a new client
            app = ClientStreamer(root, server_addr, server_port, rtp_address, rtp_port, path_to_filename)
            app.master.title("RTP Client")
            root.wait_visibility()
            root.mainloop()
            sleep(2)
