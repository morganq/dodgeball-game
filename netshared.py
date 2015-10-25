DEFAULT_SERVER_LISTEN_PORT = 2011
DEFAULT_CLIENT_LISTEN_PORT = 2012

import pickle
import socket
from player import Player
from ball import Ball
from supernode import *
from averageddata import *
import zlib
import g
import pygame
from collections import defaultdict

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

		self.packet_outbound_last_id = defaultdict(lambda:0)
		self.packet_inbound_last_id = defaultdict(lambda:0)
		self.packetloss = defaultdict(lambda:0)

		self.averagedData = AveragedData()

		self.netinfotimer = 1.0

	def readPacket(self, info, data):
		unpacked = pickle.loads(zlib.decompress(data))

		addr, port = info
		addrportstr = addr + ":" + str(port)
		pid = unpacked["packet_id"]
		lid = self.packet_inbound_last_id[addrportstr]
		if pid > lid + 1:
			self.packetloss[addrportstr] += 1
		self.packet_inbound_last_id[addrportstr] = pid

		self.averagedData.add(self.t, "packets")
		self.averagedData.add(self.t, "packetsize", len(data))

		if self.packet_inbound_last_id[addrportstr] > 0:
			packetloss = self.packetloss[addrportstr] / float(self.packet_inbound_last_id[addrportstr])
			self.averagedData.add(self.t, "packetloss_" + addrportstr, packetloss)

		return [unpacked]

	def sendPacket(self, data, addr, port):
		addrportstr = addr + ":" + str(port)
		data["packet_id"] = self.packet_outbound_last_id[addrportstr]
		self.packet_outbound_last_id[addrportstr] += 1
		self.sock.sendto(zlib.compress(pickle.dumps(data, 2)), (addr, port))

	def update(self, game, dt):
		self.game = game
		
		self.t = pygame.time.get_ticks() / 1000.0

		self.packetsPerSecond = self.averagedData.get_ct(self.t, "packets", 1.0)
		self.packetSize = self.averagedData.get_avg(self.t, "packetsize", 5.0)

		allPackets = []
		try:
			(data, info) = self.sock.recvfrom(4096)
			#self.packetSize = len(data)
			allPackets = self.readPacket(info, data)
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