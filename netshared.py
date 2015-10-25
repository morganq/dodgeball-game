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
		self.sock.settimeout(0.01)
		self.packetSize = 0
		self.t = 0
		
		self.buf = ""

		self.packetTimestamps = []
		self.packetsPerSecond = 0
		
		self.simulatedLatency = 0
		self.simulatedRandomLatency = 0
		self.simulatedRandomLatencyVal = 0
		self.simulatedPacketloss = 0
		self.simulatedPackets = []

		self.packet_outbound_last_id = defaultdict(lambda:0)
		self.packet_inbound_last_id = defaultdict(lambda:0)
		self.packetloss = defaultdict(lambda:0)

		self.ensured_send_packet_ids = defaultdict(lambda:0)
		self.ensured_sent_packets = defaultdict(dict)
		self.ensured_recv_packet_ids = defaultdict(lambda:-1)
		self.ensured_packets_received_early = defaultdict(list)
		self.resend_unconfirmed_timer = 0

		self.averagedData = AveragedData()

		self.netinfotimer = 1.0

		self.debug_lines = []

	def readPacket(self, info, data):
		self.averagedData.add(self.t, "packets")
		self.averagedData.add(self.t, "packetsize", len(data))
		unpacked = pickle.loads(zlib.decompress(data))

		addr, port = info
		addrportstr = addr + ":" + str(port)

		if "ensured_id" in unpacked:
			if unpacked["ensured_id"] == self.ensured_recv_packet_ids[addrportstr]+1:
				print "recv " + str(unpacked["ensured_id"])
				self.ensured_recv_packet_ids[addrportstr] += 1
				self.sendReceipt(addr, port, unpacked["ensured_id"])
			elif unpacked["ensured_id"] < self.ensured_recv_packet_ids[addrportstr]+1:
				print unpacked
				print "got ensured packet twice; resending receipt for " + str(unpacked["ensured_id"])
				self.sendReceipt(addr, port, unpacked["ensured_id"])
				return []
			else:
				print "got packet " + str(unpacked["ensured_id"]) + " before " + str(self.ensured_recv_packet_ids[addrportstr]+1)
				self.ensured_packets_received_early[addrportstr].append(unpacked)
				return []

		allPackets = []
		to_remove = []
		for p in self.ensured_packets_received_early[addrportstr]:
			print "resolving old " + str(unpacked["ensured_id"])
			if p["ensured_id"] == self.ensured_recv_packet_ids[addrportstr]+1:
				self.ensured_recv_packet_ids[addrportstr] += 1
				self.sendReceipt(addr, port, unpacked["ensured_id"])
				allPackets.extend(self.readUnpackedPacket(p, addrportstr))
				to_remove.append(p)
		for p in to_remove:
			self.ensured_packets_received_early[addrportstr].remove(p)

		allPackets.extend(self.readUnpackedPacket(unpacked, addrportstr))
		return allPackets

	def sendReceipt(self, addr, port, q):
		self.sendPacket({"type":"confirmReceipt","other_ensured_id":q}, addr, port)

	def readUnpackedPacket(self, unpacked, addrportstr):
		pid = unpacked["packet_id"]
		lid = self.packet_inbound_last_id[addrportstr]
		if pid > lid + 1:
			self.packetloss[addrportstr] += 1
		self.packet_inbound_last_id[addrportstr] = pid

		if self.packet_inbound_last_id[addrportstr] > 0:
			packetloss = self.packetloss[addrportstr] / float(self.packet_inbound_last_id[addrportstr])
			self.averagedData.add(self.t, "packetloss_" + addrportstr, packetloss)

		return [unpacked]

	def sendPacket(self, data, addr, port):
		addrportstr = addr + ":" + str(port)
		data["packet_id"] = self.packet_outbound_last_id[addrportstr]
		self.packet_outbound_last_id[addrportstr] += 1
		self.sock.sendto(zlib.compress(pickle.dumps(data, 2)), (addr, port))

	def sendEnsuredPacket(self, data, addr, port):
		addrportstr = addr + ":" + str(port)		
		ensured_id = self.ensured_send_packet_ids[addrportstr]
		print "sending ensured " + str(ensured_id)
		data["packet_id"] = self.packet_outbound_last_id[addrportstr]
		self.packet_outbound_last_id[addrportstr] += 1		
		data["ensured_id"] = ensured_id
		cdata = zlib.compress(pickle.dumps(data, 2))
		sent = {
			"id":ensured_id,
			"data":cdata,
			"info":(addr,port)
		}
		self.ensured_sent_packets[addrportstr][ensured_id] = sent
		self.sock.sendto(cdata, (addr, port))
		self.ensured_send_packet_ids[addrportstr] = ensured_id + 1

	def process_confirmReceipt(self, data, game, info):
		(addr, port) = info
		addrportstr = addr + ":" + str(port)
		pending_packets = self.ensured_sent_packets[addrportstr]
		pid = data["other_ensured_id"]
		print "got receipt for " + str(pid)
		if pid in pending_packets:
			del pending_packets[pid]
		else:
			if pid > self.ensured_send_packet_ids:
				print "got receipt for packet i haven't sent yet!!"

	def update(self, game, dt):
		self.game = game
		
		self.t = pygame.time.get_ticks() / 1000.0

		self.packetsPerSecond = self.averagedData.get_ct(self.t, "packets", 1.0)
		self.packetSize = self.averagedData.get_avg(self.t, "packetsize", 5.0)

		allPackets = []
		try:
			(data, info) = self.sock.recvfrom(4096)
			#self.packetSize = len(data)
			if self.simulatedPacketloss > 0 and random.random() < self.simulatedPacketloss:
				pass
			else:
				allPackets = self.readPacket(info, data)
		except socket.timeout:
			pass
		except socket.error as err:
			print err

		#print self.simulatedPackets
		if self.simulatedLatency == 0:
			for d in allPackets:
				self.process(d, game, info)
		else:
			off = self.simulatedLatency + self.simulatedRandomLatency * random.random()
			self.simulatedPackets.extend( [(d, off, info) for d in allPackets] )
			thisFramePackets = [ s for s in self.simulatedPackets if s[1] <= 0]
			self.simulatedPackets = [ s for s in self.simulatedPackets if s[1] > 0 ]
			for (p, t, info) in thisFramePackets:
				self.process(p, game, info)
			self.simulatedPackets = [ (s[0], s[1] - dt, s[2]) for s in self.simulatedPackets ]

		self.resend_unconfirmed_timer -= dt
		if self.resend_unconfirmed_timer <= 0:
			self.resend_unconfirmed_timer += 0.5
			for k,packets in self.ensured_sent_packets.items():
				for i,packet in packets.items():
					print "resending unreceipted packet: " + str(packet["id"])
					self.sock.sendto(packet["data"], packet["info"])


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