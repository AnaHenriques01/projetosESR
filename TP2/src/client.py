import sys
from tkinter import Tk
from ClientWorker import ClientWorker
import os

if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		serverPort = sys.argv[2]
		rtpAddress = sys.argv[3]
		rtpPort = sys.argv[4]
		fileName = sys.argv[5]	
	except:
		print("[Usage: ClientLauncher.py Server_Addr Server_Port RTP_Port Video_file_Name]\n")	
	
	if os.environ.get('DISPLAY','') == '':
		print('No display found... Using DISPLAY :0.0')
		os.environ.__setitem__('DISPLAY', ':0.0')

	root = Tk()
	
	# Create a new client
	app = ClientWorker(root, serverAddr, serverPort, rtpAddress, rtpPort, fileName)
	app.master.title("RTPClient")

	root.mainloop()