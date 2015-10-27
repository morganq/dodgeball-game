from netshared import *
from dodgeballscene import *
from player import PlayerController
import content

TIMESYNCS = 7
ENTITY_TIME_BACK = 0.3

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
			if "historical_positions" in e.netinfo:
				histpos = e.netinfo["historical_positions"]
				i = len(histpos) - 2
				while i >= 0:
					(t1, pos1) = histpos[i]
					if t1 < targettime:
						if i + 2 >= len(histpos):
							print "ono"
						(t2, pos2) = histpos[i+1]
						dt = t2 - t1
						dpos = pos2 - pos1
						mid = (targettime - t1) / dt
						#print mid
						e.position = pos1 + dpos * mid
						e.velocity.zero()
						break
					i -= 1
				print len(histpos) - i
				



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

		entity.visible = edata["visible"]

		
	def updatePlayer(self, time, player, pdata, game):
		if player is None:
			print("Player is None!")
			return
		if player is self.myPlayer:
			if self.t >= self.stun_t + self.latency and self.myPlayer.clientStunTimer <= 0:
				player.stunTimer = min(player.stunTimer, pdata["stun"] - self.latency / 2)
		else:
			player.stunTimer = pdata["stun"]
		player.knockbackVelocity = pdata["knockback"]
		player.health = pdata["health"]
		player.superTicks = pdata["superTicks"]
		player.xDirection = pdata["xDirection"]
		player.yDirection = pdata["yDirection"]

	def sendPlayerPosition(self, pos):
		self.sendToServer({"type":"playerPos", "time":self.serverTime, "x":pos.x, "y":pos.y})

	def sendDirectionInput(self, dx, dy, pos):
		self.sendToServer({"type":"directionInput", "time":self.serverTime, "dx" : dx, "dy" : dy,"x":pos.x, "y":pos.y})
		
	def sendButtonInput(self, button, pos):
		if button in ["throw", "super"]:
			self.stun_t = self.t
		self.sendToServer({"type":"buttonInput", "time":self.serverTime, "button":button,"x":pos.x, "y":pos.y})
		
	def sendPlayerInfo(self, name, exString, superString):
		self.sendEnsuredToServer({"type":"playerInfo", "name":name, "super":superString, "ex":exString})

	def sendTimeSyncRequest(self):
		self.sendToServer({"type":"timeSyncRequest", "client":self.t})

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
			ent.initialize()
			if  data["owner"] == self.cid:
				controller = PlayerController(ent, self)
				self.myPlayer = ent
				game.controller = controller

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
		player.holding = ball
		ball.held = True

	def process_throw(self, data, game, info):
		player = self.lookupEntity(game.scene, data["player"])
		ball = self.lookupEntity(game.scene, data["ball"])
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
		if p is not None:
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