import socket

port = 1112

sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
sock.bind( ("0.0.0.0", port) )

sock.listen(1)

last = 0
missed = 0

conn, addr = sock.accept()
sock.settimeout(0)

while last < 100:
	try:
		#(data, info) = sock.recvfrom(256)
		data = conn.recv(512)
		alldata = data.split("\n")
		for d in alldata:
			try:
				d = int(d)
				print d
				if (d - last) > 1:
					missed += (d-last)-1
				last = d
			except:
				pass

	except socket.error:
		pass

print str((float(missed) / float(last)) * 100) + "% packet loss"