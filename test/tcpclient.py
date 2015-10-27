import socket
import time

addr = "192.168.1.12"
port = 1112

sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
sock.connect((addr, port))

for i in range(110):
	sock.send(str(i)+"\n")
	print i
	time.sleep(0.025)