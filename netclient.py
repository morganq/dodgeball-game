from netshared import *
from dodgeballscene import *
from player import PlayerController
import content
import math

TIMESYNCS = 7
ENTITY_TIME_BACK = 0.25

class NetClient(NetCommon):
	def __init__(self, listenPort = DEFAULT_CLIENT_LISTEN_PORT):
		NetCommon.__init__(self, listenPort)
		self.sendAddr = None
		self.sendPort = None

		self.cid = None
		self.timeSinceUpdate = 0

		self.latency = 0
		self.pingTimestamp = 0
		self.pingTimer = 0

		self.playerPosUpdateTimer = 0
		
		self.myPlayer = None

		self.stun_t = 0
		self.serverTime = 0
		self.serverTimeOffsetFromClientTime = 0
		self.timeSyncResponses = []
		self.timeSyncTimer = 0.5

	def lookupEntity(self, scene, netid):
		for e in scene.sceneEntities:
			if "netid" in e.netinfo and e.netinfo["netid"] == netid:
				return e

	def update(self, game, dt):
		NetCommon.update(self, game, dt)
		self.serverTime = self.t + self.serverTimeOffsetFromClientTime

		self.timeSinceUpdate += dt

		if len(self.timeSyncResponses) < TIMESYNCS:
			self.timeSyncTimer -= dt
			if self.timeSyncTimer <= 0:
				self.timeSyncTimer += 0.5
				self.sendTimeSyncRequest()

		self.pingTimer -= dt
		if self.pingTimer <= 0:
			self.pingTimer += 2
			self.sendPing()

		if self.myPlayer:
			self.playerPosUpdateTimer -= dt
			if self.playerPosUpdateTimer <= 0:
				self.playerPosUpdateTimer += 0.25
				self.sendPlayerPosition(self.myPlayer.position)

		targettime = self.serverTime - ENTITY_TIME_BACK
		for e in game.scene.sceneEntities:
			serverAuthority = 1.0
			if e.name == "ball" and e.thrower == self.myPlayer and "throwClientTime" in e.netinfo:
				pass
			elif "historical_positions" in e.netinfo:
				histpos = e.netinfo["historical_positions"]
				i = len(histpos) - 2
				while i >= 0:
					(t1, pos1) = histpos[i]
					if t1 < targettime:
						if i + 2 >= len(histpos):
							#print "ono"
							pass
						(t2, pos2) = histpos[i+1]
						dt = t2 - t1
						dpos = pos2 - pos1
						mid = (targettime - t1) / dt
						#print mid
						if e.name == "ball":
							e.position = pos1 + dpos * mid
							#e.velocity = pos * dt
							#e.velocity.zero()
						if e.name == "player":
							offset = pos2 - e.position
							dist = offset.length()
							if dist > 4:
								e.xDirection = round(round(offset.x / dist * 2) / 2)
								e.yDirection = round(round(offset.y / dist * 2) / 2)
							else:
								e.xDirection = 0
								e.yDirection = 0
						break
					i -= 1
				#print e.name, len(histpos) - i
				



	def connect(self, addr, port = DEFAULT_SERVER_LISTEN_PORT):
		self.sendAddr = addr
		self.sendPort = port
		self.sendEnsuredToServer( {"type":"hello"} )
		print("Connecting...")

	def sendToServer(self, data):
		self.sendPacket(data, self.sendAddr, self.sendPort)

	def sendEnsuredToServer(self, data):
		self.sendEnsuredPacket(data, self.sendAddr, self.sendPort)		

	def sendPing(self):
		self.pingTimestamp = self.t
		self.sendToServer({"type":"ping"})

	def updateEntity(self, time, entity, edata, game):
		if entity is None:
			print("Entity is None!")
			return
		if entity == self.myPlayer:
			pass
		else:
			timeAgo = self.serverTime - time
			if "historical_positions" not in entity.netinfo:
				entity.netinfo["historical_positions"] = []
			entity.netinfo["historical_positions"].append((time, Vector2(*edata["position"])))
			entity.netinfo["historical_positions"] = filter(lambda x:x[0] > self.serverTime - 3, entity.netinfo["historical_positions"])

			if entity.name == "ball" and entity.thrower == self.myPlayer and "throwClientTime" in entity.netinfo:
				if "throwServerTime" in entity.netinfo:
					ballAgo = timeAgo + (entity.netinfo["throwServerTime"] - entity.netinfo["throwClientTime"])
					oldState = entity.getOldState(ballAgo)
					authPos = Vector2(*edata["position"])
					authVel = Vector2(*edata["velocity"])
					#print entity.position, authPos, oldState["position"]
					offset = (authPos - oldState["position"]) / 2
					voffset = (authVel - oldState["velocity"]) / 2
					#if offset.lengthSquared() > 8*8:
					#print "FIX"
					entity.position += offset
					entity.velocity += voffset
					entity.reviseHistory({"position":offset, "velocity":voffset})
					#del entity.netinfo["throwClientTime"]
					#del entity.netinfo["throwServerTime"]

		entity.visible = edata["visible"]

		
	def updatePlayer(self, time, player, pdata, game):
		if player is None:
			print("Player is None!")
			return
		if player is self.myPlayer:
			pass
			#if self.t >= self.stun_t + self.latency and self.myPlayer.clientStunTimer <= 0:
			#	player.stunTimer = min(player.stunTimer, pdata["stun"] - self.latency / 2)
		else:
			player.stunTimer = pdata["stun"]
		player.knockbackVelocity = pdata["knockback"]
		player.health = pdata["health"]
		player.superTicks = pdata["superTicks"]
		#player.xDirection = pdata["xDirection"]
		#player.yDirection = pdata["yDirection"]

	def sendPlayerPosition(self, pos):
		self.sendToServer({"type":"playerPos", "time":self.serverTime, "x":pos.x, "y":pos.y})

	def sendDirectionInput(self, dx, dy, pos):
		self.sendToServer({"type":"directionInput", "time":self.serverTime, "dx" : dx, "dy" : dy,"x":pos.x, "y":pos.y})
		
	def sendButtonInput(self, button, pos):
		if button in ["throw", "super"]:
			self.stun_t = self.t
			# TEST
			if self.myPlayer.holding:
				self.myPlayer.holding.netinfo["throwClientTime"] = self.serverTime
				self.myPlayer.tryThrow(button=="super")
			else:
				self.myPlayer.tryThrow(button=="super")
			
		self.sendToServer({"type":"buttonInput", "time":self.serverTime, "button":button,"x":pos.x, "y":pos.y})
		
	def sendPlayerInfo(self, name, exString, superString):
		self.sendEnsuredToServer({"type":"playerInfo", "name":name, "super":superString, "ex":exString})

	def sendTimeSyncRequest(self):
		self.sendToServer({"type":"timeSyncRequest", "client":self.t})

	def process_badClientSideCatch(self, data, game, info):
		if self.myPlayer.holding:
			print "bad catch!!"
			self.myPlayer.holding.held = False
			self.myPlayer.holding = None

	def process_timeSyncResponse(self, data, game, info):
		orig = data["client"]
		now = self.t
		lat = (now - orig)
		self.serverTimeOffsetFromClientTime = (data["server"] - data["client"]) - lat / 2
		self.timeSyncResponses.append(self.serverTimeOffsetFromClientTime)
		if len(self.timeSyncResponses) >= TIMESYNCS:
			self.timeSyncResponses.sort()
			self.serverTimeOffsetFromClientTime = self.timeSyncResponses[2]
			self.serverTime = self.t + self.serverTimeOffsetFromClientTime

	def process_start(self, data, game, info):
		game.setScene(DodgeballScene())
		game.started = True
		game.pauseInput = False
		
	def process_numplayers(self, data, game, info):
		game.scene.playersInGame = data["value"]

	def process_spawn(self, data, game, info):
		entName = data["name"]
		ctor = self.netEntities[entName]
		ent = ctor(data["position"], *data["args"])
		ent.netinfo = data["netinfo"]
		game.scene.add(ent)

		if data["name"] == "player":
			if  data["owner"] == self.cid:
				controller = PlayerController(ent, self)
				self.myPlayer = ent
				game.controller = controller
			ent.initialize()

	def process_id(self, data, game, info):
		self.cid = data["cid"]
		if data["admin"]:
			game.admin = True
		print("Connected.")

	def process_state(self, data, game, info):
		#print self.serverTime - data["time"]
		self.simulatedRandomLatency = self.simulatedRandomLatencyVal
		self.timeSinceUpdate = 0
		for edata in data["entities"]:
			entity = self.lookupEntity(game.scene, edata["netid"])
			if entity:
				self.updateEntity(data["time"], entity, edata, game)
			#print edata
		for pdata in data["players"]:
			player = self.lookupEntity(game.scene, pdata["netid"])
			if player:
				self.updatePlayer(data["time"], player, pdata, game)

	def process_pickup(self, data, game, info):
		player = self.lookupEntity(game.scene, data["player"])
		ball = self.lookupEntity(game.scene, data["ball"])
		if "throwServerTime" in ball.netinfo:
			del ball.netinfo["throwServerTime"]
		if "throwClientTime" in ball.netinfo:
			del ball.netinfo["throwClientTime"]
		player.holding = ball
		ball.held = True

	def process_throw(self, data, game, info):
		player = self.lookupEntity(game.scene, data["player"])
		ball = self.lookupEntity(game.scene, data["ball"])
		if player == self.myPlayer and "throwClientTime" in ball.netinfo:
			print "got my throw mess"
			ball.netinfo["throwServerTime"] = data["time"]
			return		
		player.holding = None
		ball.velocity = data["velocity"]
		ball.zVelocity = data["zVelocity"]
		ball.throwTeam = data["team"]
		ball.mode = data["mode"]
		ball.held = False

	def process_chat(self, data, game, info):
		p = self.lookupEntity(game.scene, data["netid"])
		if p is not None:
			p.chatText = data["text"]
			p.chatTimer = 5
		
	def process_animation(self, data, game, info):
		p = self.lookupEntity(game.scene, data["netid"])
		if p is not None and p is not self.myPlayer:
			p.play(data["name"])

	def process_endround(self, data, game, info):
		game.score = data["score"]
		if data["winner"] == self.myPlayer.team:
			game.scene.victoryMessage = "Victory!"
			content.sounds["victory.wav"].play()
		else:
			game.scene.victoryMessage = "Defeat."
			content.sounds["defeat.wav"].play()
			
	def process_sound(self, data, game, info):
		content.sounds[data["name"]].play()

	def process_pong(self, data, game, info):
		self.averagedData.add(self.t, "latency", self.t - self.pingTimestamp)
		self.latency = self.averagedData.get_avg(self.t, "latency", 10)