import socket
import time

addr = "192.168.1.17"
port = 1112

sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )

for i in range(1100):
	sock.sendto(str(i), (addr, port))
	time.sleep(0.001)