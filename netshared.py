DEFAULT_SERVER_LISTEN_PORT = 2011
DEFAULT_CLIENT_LISTEN_PORT = 2012

import pickle
import socket
from player import Player
from ball import Ball
from supernode import *
import zlib
import g
import pygame

class NetCommon:
	netEntities = { "player": Player, "ball": Ball }
	def __init__(self, listenPort):
		#Make a UDP socket
		self.sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
		self.sock.bind( ("0.0.0.0", listenPort) )
		self.sock.settimeout(0)
		self.packetSize = 0
		self.t = 0
		
		self.buf = ""

		self.packetTimestamps = []
		self.packetsPerSecond = 0
		
		self.simulatedLatency = 0
		self.simulatedPackets = []

	def readPacket(self, data):
		p = []
#		for pack in data.split("\n\n"):
#			self.packetsThisSecond += 1
#			if len(pack) > 0:
#				try:
#					p.append(pickle.loads(zlib.decompress(pack)))
#				except:
#					print("Failed to read packet, saving for next frame.")
#					self.buf += pack
		p.append(pickle.loads(zlib.decompress(data)))
		self.packetTimestamps.append(self.t)
		return p

	def sendPacket(self, data, addr, port):
		self.sock.sendto(zlib.compress(pickle.dumps(data, 2)), (addr, port))

	def update(self, game, dt):
		self.game = game
		
		self.t = pygame.time.get_ticks() / 1000.0

		self.packetTimestamps = filter(lambda x:x > self.t-1, self.packetTimestamps)
		self.packetsPerSecond = len(self.packetTimestamps)

		#print self.packetsPerSecond

		allPackets = []
		try:
			(data, info) = self.sock.recvfrom(4096)
			#self.packetSize = len(data)
			allPackets = self.readPacket(data)
		except(socket.error):
			pass

		#print self.simulatedPackets
		if self.simulatedLatency == 0:
			for d in allPackets:
				self.process(d, game, info)
		else:
			self.simulatedPackets.extend( [(d, self.simulatedLatency, info) for d in allPackets] )
			thisFramePackets = [ s for s in self.simulatedPackets if s[1] <= 0]
			self.simulatedPackets = [ s for s in self.simulatedPackets if s[1] > 0 ]
			for (p, t, info) in thisFramePackets:
				self.process(p, game, info)
			self.simulatedPackets = [ (s[0], s[1] - dt, s[2]) for s in self.simulatedPackets ]

	def process(self, data, game, info):
		if(hasattr(self, "process_" + data["type"])):
			f = getattr(self, "process_" + data["type"])
			f(data, game, info)
		else:
			print("Got packet of type '" + data["type"] + "' but there is no process_" + data["type"] + " method to handle it." )
			
	def constructSuper(self, superString, cost = 99999, nid = -1):
		s = []
		for c in superString.lower():
			ctor = allnodes[c]
			cost -= ctor.cost
			s.append(ctor(self.game))
		if cost < 0:
			s = []
		if g.SERVER:
			if nid != -1:
				self.broadcast({"type":"chat", "text":str(cost), "netid":nid})
		return s