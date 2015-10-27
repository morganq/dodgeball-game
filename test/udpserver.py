import socket

port = 1112

sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
sock.bind( ("0.0.0.0", port) )
sock.settimeout(0)

last = 0
missed = 0

while last < 100:
	try:
		(data, info) = sock.recvfrom(4096)
		d = int(data)
		print d
		if (d - last) > 1:
			missed += (d-last)-1
		last = d

	except socket.error:
		pass

print str((float(missed) / float(last)) * 100) + "% packet loss"