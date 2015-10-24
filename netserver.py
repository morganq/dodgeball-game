from player import Player
from vector2 import Vector2
from netshared import *
from dodgeballscene import *
from ball import Ball
import supernode

import random
import socket
import time

try:
	import win32com
	import win32com.client
except:
	pass

class ClientInfo:
	def __init__(self, cid, addr, port, entity):
		self.cid = cid
		self.addr = addr
		self.port = port
		self.name = "player"
		self.entity = entity
		self.latency = 0
		self.pingTimestamp = 0
		self.admin = False
		self.super = []
		self.exThrow = []


class NetServer(NetCommon):
	def __init__(self, listenPort=DEFAULT_SERVER_LISTEN_PORT):
		NetCommon.__init__(self, listenPort)
		self.clients = []

		self.stateUpdateTimer = 0

		self.netidcounter = 0
		self.allentities = []
		self.ended = False

		self.score = [0,0]

		try:
			natter = win32com.client.Dispatch("HNetCfg.NATUPnP")
			mappingPorts = natter.StaticPortMappingCollection
			mappingPorts.Add(listenPort, "UDP", listenPort, socket.gethostbyname(socket.gethostname()), True, "DodgeballServer")
		except:
			print("Everything's fine. Don't worry about it.")

	def sendToClient(self, client, data):
		self.sendPacket(data, client.addr, client.port)

	def update(self, game, dt):
		NetCommon.update(self, game, dt)
		if(game.started):
			self.stateUpdateTimer -= dt
			if self.stateUpdateTimer < 0:
				self.stateUpdateTimer = 0.25 + self.stateUpdateTimer
				self.sendStateUpdate(game)

			if self.ended:
				self.nextRoundTimer -= dt
				if self.nextRoundTimer <= 0:
					self.startRound(game)
			else:
				#Check for victory condition
				teams = [0, 0]
				if len(self.clients) > 1:
					for c in self.clients:
						if c.entity.health > 0:
							teams[c.entity.team] += 1
					if teams[0] == 0:
						self.endRound(1)
					elif teams[1] == 0:
						self.endRound(0)
					game.score = self.score

	def endRound(self, winner):
		self.score[winner] += 1
		self.broadcast({"type":"endround", "winner": winner, "score":self.score})
		self.ended = True
		self.nextRoundTimer = 5.0

	def sendStateUpdate(self, game):
		data = {"type":"state", "entities":[], "players":[]}
		for e in game.scene.sceneEntities:
			if not "ignore" in e.netinfo and "netid" in e.netinfo:
				entity_data = self.getEntityStateData(e)
				if entity_data:
					data["entities"].append( entity_data )
		for c in self.clients:
			data["players"].append( self.getPlayerStateData(c.entity) )
		self.broadcast(data)

	def getPlayerStateData(self, p):
		data = {}
		data["netid"] = p.netinfo["netid"]
		data["xDirection"] = p.xDirection
		data["yDirection"] = p.yDirection
		data["health"] = int(p.health)
		data["stun"] = p.stunTimer
		data["superTicks"] = p.superTicks
		data["knockback"] = p.knockbackVelocity
		return data

	def getEntityStateData(self, e):
		data = {}
		data["netid"] = e.netinfo["netid"]
		data["position"] = e.position.asIntTuple()
		data["velocity"] = e.velocity.asIntTuple()
		data["z"] = int(e.z)
		data["zVelocity"] = int(e.zVelocity)
		data["visible"] = e.visible
		if "teleporting" in e.netinfo and e.netinfo["teleporting"]:
			data["teleporting"] = True
			e.netinfo["teleporting"] = False
		else:
			data["teleporting"] = False
		return data

	def broadcast(self, data):
		for c in self.clients:
			self.sendPacket(data, c.addr, c.port)

	def spawn(self, ent, name, extra = {}):
		ent.netinfo["netid"] = self.netidcounter
		self.allentities.append(ent)
		self.netidcounter += 1
		data = {"type":"spawn", "name":name, "position":ent.position, "netinfo":ent.netinfo, "args" : []}
		for k, v in extra.items():
			data[k] = v
		self.broadcast(data)

	def sendPickupMessage(self, player, ball):
		self.broadcast({"type":"pickup", "player":player.netinfo["netid"], "ball":ball.netinfo["netid"]})

	def sendThrowMessage(self, player, ball, velocity, zVel, mode):
		self.broadcast({"type":"throw", "player":player.netinfo["netid"], "ball":ball.netinfo["netid"],
		"velocity":velocity, "zVelocity": zVel, "mode":mode, "team":player.team})

	def startRound(self, game):
		self.broadcast({"type":"start"})
		self.ended = False
		game.started = True
		game.setScene(DodgeballScene())
		i = 0
		for c in self.clients:
			p = c.entity
			# figure out which team each player is on and how to position them.
			p.team = i % 2
			if p.team == 0:
				p.position.x = 80 - int(i/2) * 7
			else:
				p.position.x = 240 + int(i/2) * 7
			p.position.y = int(i / 2) * 36 + 40
			i += 1
			game.scene.add(p)
			p.initialize()
			p.exThrow = c.exThrow
			p.super = c.super
			self.spawn(p, "player", {"owner":c.cid, "args":[p.team]})
		for i in range(3):
			b = Ball(Vector2(random.randint(50, 290), random.randint(50, 180)))
			game.scene.add(b)
			self.spawn(b, "ball")

	def getClient(self, info):
		for c in self.clients:
			if info == (c.addr, c.port):
				return c
				
	def sendSoundMessage(self, name):
		self.broadcast({"type":"sound", "name":name})

	def process_pregame_hello(self, data, game, info):
		self.broadcast({"type":"numplayers","value":len(self.clients)})
		print(info[0] + " joined the game.")
		game.scene.playersInGame += 1

	def process_ingame_hello(self, data, game, info, player, client):
		self.startRound(game)

	def process_hello(self, data, game, info):
		for c in self.clients:
			if c.addr == info[0] and c.port == info[1]:
				print("Client can't connect a second time.")
				return

		player = Player(Vector2(0,0))
		c = ClientInfo(len(self.clients), info[0], info[1], player)
		if len(self.clients) == 0:
			c.admin = True
		self.clients.append(c)
		self.sendToClient(c, {"type": "id", "cid": c.cid, "admin":c.admin} )

		if not game.started:
			self.process_pregame_hello(data, game, info)

		else:
			self.process_ingame_hello(data, game, info, player, c)



	def process_start(self, data, game, info):
		c = self.getClient(info)
		if c is None or not c.admin:
			return
		self.startRound(game)


	def process_directionInput(self, data, game, info):
		c = self.getClient(info)
		if c is None:
			return
		c.entity.xDirection = data["x"]
		c.entity.yDirection = data["y"]
		c.entity.tryDash((data["x"], data["y"]))

	def process_buttonInput(self, data, game, info):
		c = self.getClient(info)
		if c is None:
			return
		if data["button"] == "throw":
			c.entity.tryThrow(False)
		if data["button"] == "super":
			c.entity.tryThrow(True)
		if data["button"] == "jump":
			c.entity.tryJump()

	def process_playerInfo(self, data, game, info):
		c = self.getClient(info)
		if c is None:
			return
		c.super = self.constructSuper(data["super"], 100)
		c.exThrow = self.constructSuper(data["ex"], 15)
		c.name = data["name"]
		print(c.addr + " identified as " + c.name)

	def process_chat(self, data, game, info):
		c = self.getClient(info)
		c.entity.chatText = data["text"]
		c.entity.chatTimer = 5
		chat = True
		if data["text"].startswith("/super "):
			try:
				c.super = self.constructSuper(data["text"][7:], 100, c.entity.netinfo["netid"])
				c.entity.super = c.super
				chat = False
			except:
				pass
		if data["text"].startswith("/ex "):
			try:
				c.exThrow = self.constructSuper(data["text"][4:], 15, c.entity.netinfo["netid"])
				c.entity.exThrow = c.exThrow
				chat = False
			except:
				pass
		if data["text"] == "/nodes":
			data["text"] = "".join([cl.symbol for cl in supernode.allnodes.values()])
		if chat:
			self.broadcast({"type":"chat", "text":data["text"], "netid":c.entity.netinfo["netid"]})

	def process_ping(self, data, game, info):
		c = self.getClient(info)
		self.sendToClient(c, {"type":"pong"})